
import { WebSocketClient } from "./client.js";

/**
 * Djangospice event-based WebSocket client.
 */
export class RealtimeClient {
    constructor(path, options = {}) {
        this.listeners = new Map();

        this.transport = new WebSocketClient(path, {
            ...options,

            onStatus: (status, detail) => {
                this.emit("connection.status", {
                    status,
                    detail,
                });

                options.onStatus?.(status, detail);
            },

            onMessage: (message) => {
                if (
                    !message ||
                    typeof message !== "object" ||
                    Array.isArray(message) ||
                    typeof message.event !== "string"
                ) {
                    this.emit(
                        "connection.invalid_message",
                        message,
                    );
                    return;
                }

                this.emit(message.event, message.data);
                this.emit("*", message);
            },
        });
    }

    /**
     * Subscribe to an event.
     * Returns an unsubscribe function.
     */
    on(event, callback) {
        if (typeof callback !== "function") {
            throw new TypeError(
                "Djangospice RealtimeClient: callback must be a function.",
            );
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(callback);

        return () => this.off(event, callback);
    }

    /**
     * Subscribe to an event once.
     */
    once(event, callback) {
        let unsubscribe;

        unsubscribe = this.on(event, (data) => {
            unsubscribe();
            callback(data);
        });

        return unsubscribe;
    }

    off(event, callback) {
        const callbacks = this.listeners.get(event);

        if (!callbacks) return;

        callbacks.delete(callback);

        if (callbacks.size === 0) {
            this.listeners.delete(event);
        }
    }

    emit(event, data) {
        const callbacks = this.listeners.get(event);

        if (!callbacks) return;

        for (const callback of [...callbacks]) {
            try {
                callback(data);
            } catch (error) {
                console.error(
                    `Djangospice: handler failed for "${event}".`,
                    error,
                );
            }
        }
    }

    connect() {
        return this.transport.connect();
    }

    send(data) {
        return this.transport.send(data);
    }

    get connected() {
        return this.transport.connected;
    }

    disconnect() {
        this.transport.disconnect();
    }

    destroy() {
        this.disconnect();
        this.listeners.clear();
    }
}
