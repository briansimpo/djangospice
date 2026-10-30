
/**
 * Djangospice WebSocket transport.
 *
 * Responsibilities:
 * - Manage a single WebSocket connection.
 * - Reconnect after unexpected disconnections.
 * - Send and receive JSON messages.
 * - Expose connection lifecycle callbacks.
 *
 * Domain-specific event handling belongs in RealtimeClient.
 */
export class WebSocketClient {
    constructor(
        path,
        {
            onMessage,
            onStatus,
            reconnect = true,
            reconnectDelay = 1000,
            maxReconnectDelay = 30000,
            maxRetries = Infinity,
            protocols,
        } = {},
    ) {
        if (!path) {
            throw new Error(
                "Djangospice WebSocket: a path is required.",
            );
        }

        this.path = path;
        this.protocols = protocols;
        this.onMessage = onMessage;
        this.onStatus = onStatus;

        this.reconnect = reconnect;
        this.reconnectDelay = reconnectDelay;
        this.maxReconnectDelay = maxReconnectDelay;
        this.maxRetries = maxRetries;

        this.socket = null;
        this.retryTimer = null;
        this.retryCount = 0;
        this.generation = 0;
        this.closed = true;
    }

    get connected() {
        return this.socket?.readyState === WebSocket.OPEN;
    }

    connect() {
        if (
            this.socket &&
            [
                WebSocket.CONNECTING,
                WebSocket.OPEN,
            ].includes(this.socket.readyState)
        ) {
            return this.socket;
        }

        this.closed = false;
        clearTimeout(this.retryTimer);
        this.retryTimer = null;

        const generation = ++this.generation;
        const scheme =
            window.location.protocol === "https:" ? "wss:" : "ws:";

        const url = this.path.startsWith("ws://")
            || this.path.startsWith("wss://")
            ? this.path
            : `${scheme}//${window.location.host}${this.path.startsWith("/") ? "" : "/"}${this.path}`;

        let socket;

        try {
            socket = this.protocols
                ? new WebSocket(url, this.protocols)
                : new WebSocket(url);
        } catch (error) {
            this.emitStatus("error", error);
            this.scheduleReconnect(generation);
            return null;
        }

        this.socket = socket;
        this.emitStatus("connecting");

        socket.onopen = () => {
            if (generation !== this.generation) return;

            this.retryCount = 0;
            this.emitStatus("connected");
        };

        socket.onmessage = (event) => {
            if (generation !== this.generation) return;

            let data;

            try {
                data = JSON.parse(event.data);
            } catch {
                data = event.data;
            }

            try {
                this.onMessage?.(data);
            } catch (error) {
                this.emitStatus("handler_error", error);
            }
        };

        socket.onerror = (error) => {
            if (generation === this.generation) {
                this.emitStatus("error", error);
            }
        };

        socket.onclose = (event) => {
            if (generation !== this.generation) return;

            this.socket = null;
            this.emitStatus("disconnected", event);

            this.scheduleReconnect(generation);
        };

        return socket;
    }

    scheduleReconnect(generation) {
        if (
            this.closed ||
            !this.reconnect ||
            generation !== this.generation ||
            this.retryCount >= this.maxRetries
        ) {
            return;
        }

        const delay = Math.min(
            this.reconnectDelay * 2 ** this.retryCount,
            this.maxReconnectDelay,
        );

        this.retryCount++;

        this.retryTimer = setTimeout(() => {
            if (!this.closed && generation === this.generation) {
                this.connect();
            }
        }, delay);
    }

    send(data) {
        if (!this.connected) {
            return false;
        }

        const payload =
            typeof data === "string"
                ? data
                : JSON.stringify(data);

        this.socket.send(payload);
        return true;
    }

    disconnect(code = 1000, reason = "Client disconnected") {
        this.closed = true;
        this.generation++;

        clearTimeout(this.retryTimer);
        this.retryTimer = null;

        const socket = this.socket;
        this.socket = null;

        if (
            socket &&
            socket.readyState !== WebSocket.CLOSED
        ) {
            socket.close(code, reason);
        }

        this.emitStatus("disconnected");
    }

    emitStatus(status, detail = null) {
        this.onStatus?.(status, detail);
    }
}
