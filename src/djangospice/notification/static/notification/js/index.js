
(function (global) {
    "use strict";

    const Djangospice = global.Djangospice ??= {};

    const EVENT_TYPES = [
        "notification_created",
        "notification_read",
        "notification_unread",
        "notification_deleted",
    ];

    class Notification {
        constructor() {
            this.listeners = new Map();
            this.initialized = false;
            this.realtime = null;
            this.realtimeHandlers = [];
        }

        initialize() {
            if (this.initialized) return this;

            this.bindRealtimeEvents();
            this.initialized = true;

            return this;
        }

        /**
         * Normalize serialized Python values recursively.
         */
        normalize(value) {
            if (value === null || value === undefined) {
                return value;
            }

            if (Array.isArray(value)) {
                return value.map(item => this.normalize(item));
            }

            if (typeof value !== "object") {
                return value;
            }

            if (value.__type__ === "dataclass") {
                return this.normalize(value.data);
            }

            if (value.__type__ === "uuid_primitive") {
                return value.value;
            }

            return Object.fromEntries(
                Object.entries(value).map(([key, item]) => [
                    key,
                    this.normalize(item),
                ])
            );
        }

        /**
         * Subscribe to original server event names.
         */
        bindRealtimeEvents() {
            const realtime = Djangospice.Realtime;

            if (!realtime || this.realtime === realtime) return;

            this.realtime = realtime;

            for (const eventName of EVENT_TYPES) {
                const handler = event => {
                    this.handleRealtimeEvent(eventName, event);
                };

                realtime.on(eventName, handler);

                this.realtimeHandlers.push([
                    eventName,
                    handler,
                ]);
            }
        }

        /**
         * Forward the complete normalized server payload.
         */
        handleRealtimeEvent(eventName, event) {
            const payload = this.normalize(event?.data ?? event);

            if (!payload || typeof payload !== "object") {
                return;
            }

            this.emit(eventName, payload);
        }

        on(event, callback) {
            if (typeof callback !== "function") {
                throw new TypeError(
                    "Notification listener must be a function."
                );
            }

            if (!this.listeners.has(event)) {
                this.listeners.set(event, new Set());
            }

            this.listeners.get(event).add(callback);

            return () => this.off(event, callback);
        }

        off(event, callback) {
            this.listeners.get(event)?.delete(callback);
        }

        emit(event, data = null) {
            this.listeners.get(event)?.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(
                        `Notification listener failed (${event}):`,
                        error
                    );
                }
            });
        }

        destroy() {
            if (this.realtime) {
                for (const [event, handler] of this.realtimeHandlers) {
                    this.realtime.off?.(event, handler);
                }
            }

            this.realtimeHandlers = [];
            this.realtime = null;
            this.listeners.clear();
            this.initialized = false;
        }
    }

    Djangospice.NotificationClass ??= Notification;
    Djangospice.Notification ??= new Notification();

})(globalThis);
