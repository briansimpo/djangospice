
(function (global) {
    "use strict";

    const Djangospice = global.Djangospice ??= {};

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

        bindRealtimeEvents() {
            const realtime = Djangospice.Realtime;

            if (!realtime || this.realtime === realtime) return;

            this.realtime = realtime;

            const handler = event => {
                const notification =
                    event?.notification ??
                    event?.data?.notification ??
                    event?.data ??
                    event;

                if (!notification) return;

                this.emit("created", notification);
            };

            realtime.on("notification_created", handler);

            this.realtimeHandlers.push([
                "notification_created",
                handler,
            ]);
        }

        on(event, callback) {
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


