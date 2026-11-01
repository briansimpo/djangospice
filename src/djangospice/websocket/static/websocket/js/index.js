
/**
 * Djangospice Realtime
 *
 * Native WebSocket abstraction.
 * Public API: Djangospice.Realtime
 */

(function (global) {
    "use strict";

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

    class RealtimeManager {
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

            // Start with the current page's URL.
            const url = new URL(path, window.location.href);

            // Automatically select the WebSocket protocol.
            url.protocol = protocol || (
                window.location.protocol === "https:"
                    ? "wss:"
                    : "ws:"
            );

            // Use the current hostname unless explicitly overridden.
            if (host) {
                url.hostname = host;
            }

            // null means use the current page's port.
            // An explicit port overrides it.
            if (port !== null && port !== undefined) {
                url.port = String(port);
            }

            return url.toString();
        }


        // Connection

        connect() {
            const WebSocketClass = global.WebSocket;

            if (!WebSocketClass) {
                return Promise.reject(
                    new Error("Realtime: WebSocket is not supported.")
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
                    new Error("Realtime: previous connection is closing.")
                );
            }

            this.manualDisconnect = false;
            this.clearReconnectTimer();

            const generation = ++this.generation;

            this.setStatus("connecting");

            // Construct the socket before creating the promise.
            // This prevents synchronous constructor errors from leaving
            // a rejected promise stored in connectionPromise.
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
                            `Realtime: connection closed (${event.code}).`
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

            // Invalidate callbacks belonging to the old connection.
            this.generation++;

            this.settleConnection?.(
                new Error("Realtime: connection cancelled.")
            );

            this.connectionPromise = null;
            this.settleConnection = null;

            const socket = this.socket;
            this.socket = null;

            if (
                socket &&
                global.WebSocket &&
                socket.readyState !== global.WebSocket.CLOSED &&
                socket.readyState !== global.WebSocket.CLOSING
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
                !global.WebSocket ||
                this.socket.readyState !== global.WebSocket.OPEN
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
                    "Realtime: listener must be a function."
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
                    global.setTimeout(() => {
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

            this.reconnectTimer = global.setTimeout(() => {
                this.reconnectTimer = null;

                this.connect().catch(() => {
                    // The next failed connection schedules another attempt.
                });
            }, delay);
        }

        clearReconnectTimer() {
            if (this.reconnectTimer !== null) {
                global.clearTimeout(this.reconnectTimer);
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
                !!global.WebSocket &&
                this.socket.readyState === global.WebSocket.OPEN
            );
        }

        get connecting() {
            return this.status === "connecting";
        }
    }

    // Public API
    // Djangospice is the global namespace shared by all Djangospice apps.

    global.Djangospice ??= {};

    const Djangospice = global.Djangospice;

    // Preserve existing registrations if this script is loaded again.
    Djangospice.RealtimeManager ??= RealtimeManager;
    Djangospice.Realtime ??= new Djangospice.RealtimeManager();

})(globalThis);
