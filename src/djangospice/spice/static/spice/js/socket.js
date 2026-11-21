/**
 * SpiceSocket
 *
 * Native WebSocket abstraction layer for Django / HTMX applications.
 * Public API: SpiceSocket (ES Module) & window.Djangospice.SpiceSocket
 */

const DEFAULT_OPTIONS = {
    path: "/ws/realtime/",
    host: null,
    port: null,
    protocol: null,
    reconnect: true,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000,
    maxRetries: Infinity,
};

export class SpiceSocket {
    constructor(options = {}) {
        this.options = {
            ...DEFAULT_OPTIONS,
            ...options,
            maxRetries: options.maxRetries === null
                ? Infinity
                : options.maxRetries ?? DEFAULT_OPTIONS.maxRetries,
        };

        this.listeners = new Map();
        this.socket = null;
        this.status = "disconnected";

        this.retries = 0;
        this.reconnectTimer = null;
        this.connectionPromise = null;
        this.settleConnection = null;

        this.manualDisconnect = false;
        this.generation = 0;
    }

    // Configuration

    configure(options = {}) {
        this.options = {
            ...this.options,
            ...options,
            maxRetries: options.maxRetries === null
                ? Infinity
                : options.maxRetries ?? this.options.maxRetries,
        };

        return this;
    }

    getUrl() {
        const {
            path,
            host,
            port,
            protocol,
        } = this.options;

        const url = new URL(path, window.location.href);

        url.protocol = protocol || (
            window.location.protocol === "https:"
                ? "wss:"
                : "ws:"
        );

        if (host) {
            url.hostname = host;
        }

        if (port !== null && port !== undefined) {
            url.port = String(port);
        }

        return url.toString();
    }

    // Connection

    connect() {
        const WebSocketClass = globalThis.WebSocket;

        if (!WebSocketClass) {
            return Promise.reject(
                new Error("SpiceSocket: WebSocket is not supported.")
            );
        }

        if (this.socket?.readyState === WebSocketClass.OPEN) {
            return Promise.resolve(this);
        }

        if (this.connectionPromise) {
            return this.connectionPromise;
        }

        if (this.socket?.readyState === WebSocketClass.CLOSING) {
            return Promise.reject(
                new Error("SpiceSocket: previous connection is closing.")
            );
        }

        this.manualDisconnect = false;
        this.clearReconnectTimer();

        const generation = ++this.generation;

        this.setStatus("connecting");

        let socket;

        try {
            socket = new WebSocketClass(this.getUrl());
            this.socket = socket;
        } catch (error) {
            this.socket = null;
            this.setStatus("disconnected", error);
            this.scheduleReconnect();

            return Promise.reject(error);
        }

        this.connectionPromise = new Promise((resolve, reject) => {
            let settled = false;

            const settle = (callback, value) => {
                if (settled) return;

                settled = true;

                if (this.generation === generation) {
                    this.connectionPromise = null;
                    this.settleConnection = null;
                }

                callback(value);
            };

            this.settleConnection = (error) => {
                settle(reject, error);
            };

            socket.addEventListener("open", (event) => {
                if (generation !== this.generation) return;

                const wasReconnecting = this.retries > 0;

                this.retries = 0;

                this.setStatus("connected", event);
                this.emit("open", event);

                if (wasReconnecting) {
                    this.emit("reconnected", event);
                }

                settle(resolve, this);
            });

            socket.addEventListener("message", (event) => {
                if (generation !== this.generation) return;

                this.handleMessage(event);
            });

            socket.addEventListener("error", (event) => {
                if (generation !== this.generation) return;

                this.emit("error", event);
            });

            socket.addEventListener("close", (event) => {
                if (generation !== this.generation) return;

                this.socket = null;

                this.setStatus("disconnected", event);
                this.emit("close", event);

                settle(
                    reject,
                    new Error(
                        `SpiceSocket: connection closed (${event.code}).`
                    )
                );

                if (!this.manualDisconnect) {
                    this.scheduleReconnect();
                }
            });
        });

        return this.connectionPromise;
    }

    disconnect(code = 1000, reason = "Client disconnected") {
        this.manualDisconnect = true;
        this.clearReconnectTimer();

        this.generation++;

        this.settleConnection?.(
            new Error("SpiceSocket: connection cancelled.")
        );

        this.connectionPromise = null;
        this.settleConnection = null;

        const socket = this.socket;
        this.socket = null;

        if (
            socket &&
            globalThis.WebSocket &&
            socket.readyState !== globalThis.WebSocket.CLOSED &&
            socket.readyState !== globalThis.WebSocket.CLOSING
        ) {
            socket.close(code, reason);
        }

        this.setStatus("disconnected");

        return this;
    }

    destroy() {
        this.disconnect();

        this.listeners.clear();
        this.retries = 0;

        return this;
    }

    // Messaging

    send(event, data = {}) {
        if (
            !this.socket ||
            !globalThis.WebSocket ||
            this.socket.readyState !== globalThis.WebSocket.OPEN
        ) {
            return false;
        }

        this.socket.send(JSON.stringify({ event, data }));

        return true;
    }

    handleMessage(message) {
        let data;

        try {
            data = JSON.parse(message.data);
        } catch {
            this.emit("message", message.data);
            return;
        }

        this.emit("message", data);

        if (
            data &&
            typeof data === "object" &&
            typeof data.event === "string"
        ) {
            this.emit(data.event, data.data);
        }
    }

    // Events

    on(event, callback) {
        if (typeof callback !== "function") {
            throw new TypeError(
                "SpiceSocket: listener must be a function."
            );
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(callback);

        return this;
    }

    once(event, callback) {
        const wrapper = (...args) => {
            this.off(event, wrapper);
            callback(...args);
        };

        return this.on(event, wrapper);
    }

    off(event, callback) {
        if (!this.listeners.has(event)) {
            return this;
        }

        if (callback) {
            const callbacks = this.listeners.get(event);

            callbacks.delete(callback);

            if (callbacks.size === 0) {
                this.listeners.delete(event);
            }
        } else {
            this.listeners.delete(event);
        }

        return this;
    }

    emit(event, ...args) {
        const callbacks = this.listeners.get(event);

        if (!callbacks) {
            return this;
        }

        for (const callback of [...callbacks]) {
            try {
                callback(...args);
            } catch (error) {
                globalThis.setTimeout(() => {
                    throw error;
                }, 0);
            }
        }

        return this;
    }

    // Reconnection

    scheduleReconnect() {
        const {
            reconnect,
            reconnectDelay,
            maxReconnectDelay,
            maxRetries,
        } = this.options;

        if (
            this.manualDisconnect ||
            !reconnect ||
            this.reconnectTimer !== null
        ) {
            return;
        }

        if (this.retries >= maxRetries) {
            this.emit("reconnect_failed", {
                attempts: this.retries,
            });

            return;
        }

        const delay = Math.min(
            reconnectDelay * Math.pow(2, this.retries),
            maxReconnectDelay
        );

        this.retries++;

        this.setStatus("reconnecting", {
            attempt: this.retries,
            delay,
        });

        this.reconnectTimer = globalThis.setTimeout(() => {
            this.reconnectTimer = null;

            this.connect().catch(() => {
                // The next failed connection schedules another attempt.
            });
        }, delay);
    }

    clearReconnectTimer() {
        if (this.reconnectTimer !== null) {
            globalThis.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    // Status

    setStatus(status, details = null) {
        const previousStatus = this.status;

        this.status = status;

        const payload = {
            status,
            previousStatus,
            details,
        };

        this.emit("status", payload);

        if (previousStatus !== status) {
            this.emit(status, payload);
        }

        return this;
    }

    // State

    get connected() {
        return (
            !!this.socket &&
            !!globalThis.WebSocket &&
            this.socket.readyState === globalThis.WebSocket.OPEN
        );
    }

    get connecting() {
        return this.status === "connecting";
    }
}



export class SpiceSocketHandler {
    constructor(socket = globalThis.spice?.socket) {
        this.socket = socket;
        this.listeners = [];
    }

    listen(event, callback) {
        if (!this.socket) {
            return this;
        }

        this.socket.on(event, callback);

        this.listeners.push({
            event,
            callback,
        });

        return this;
    }

    destroy() {
        if (this.socket) {
            this.listeners.forEach(({ event, callback }) => {
                this.socket.off(event, callback);
            });
        }

        this.listeners = [];

        return this;
    }
}
