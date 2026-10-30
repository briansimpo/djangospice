/**
 * Real-time notification store and HTTP API.
 *
 * Static namespace:
 *   notification/
 *
 * Depends on:
 *   websocket/ -> RealtimeClient
 *
 * WebSocket event envelope:
 *   {
 *     "event": "notification.created",
 *     "data": { ...notification }
 *   }
 */


export class Notification {
    /**
     * Shared notification store.
     * @type {Map<string|number, Object>}
     */
    static notifications = new Map();

    static initialized = false;

    static realtime = null;

    static config = {
        endpoints: {
            unreadList: "/notifications/api/unread/",
            allList: "/notifications/api/",
            unreadCount: "/notifications/api/unread/count/",
            allCount: "/notifications/api/count/",
            markAllRead: "/notifications/api/read-all/",
        },

        websocketPath: null,

        // Set to false if another part of the application manages WebSockets.
        realtimeEnabled: true,

        // Optional callback for connection status changes.
        onConnectionStatus: null,
    };

    static counts = {
        unread: null,
        all: null,
    };

    static unsubscribeRealtime = [];

    // ---------------------------------------------------------------------
    // Configuration and initialization
    // ---------------------------------------------------------------------

    /**
     * Configure endpoints and WebSocket options.
     *
     * Example:
     * Notification.configure({
     *     endpoints: {
     *         unreadList: "/api/notifications/unread/",
     *     },
     *     websocketPath: "/ws/notifications/",
     * });
     */
    static configure(options = {}) {
        const { endpoints, ...settings } = options;

        this.config = {
            ...this.config,
            ...settings,
            endpoints: {
                ...this.config.endpoints,
                ...(endpoints || {}),
            },
        };

        return this;
    }

    /**
     * Initialize DOM event listeners and real-time notification delivery.
     * Safe to call more than once.
     */
    static initialize(options = {}) {
        if (options && Object.keys(options).length) {
            this.configure(options);
        }

        if (this.initialized) {
            return this;
        }

        this.initialized = true;

        // Preserve support for existing application-level DOM events.
        document.addEventListener(
            "djangospice:notification_created",
            (event) => this.update(event.detail?.notification)
        );

        document.addEventListener(
            "djangospice:notification_read",
            (event) => this.update(event.detail?.notification)
        );

        document.addEventListener(
            "djangospice:notification_unread",
            (event) => this.update(event.detail?.notification)
        );

        document.addEventListener(
            "djangospice:notification_deleted",
            (event) => this.remove(event.detail?.notification)
        );

        if (this.config.realtimeEnabled && this.config.websocketPath) {
            this.connectRealtime(this.config.websocketPath);
        }

        return this;
    }

    /**
     * Connect to the notification WebSocket.
     */
    static connectRealtime(path = this.config.websocketPath) {
        if (!path) {
            throw new Error(
                "Notification WebSocket path is not configured."
            );
        }

        // Avoid creating duplicate connections.
        if (this.realtime) {
            return this.realtime;
        }

        this.realtime = new RealtimeClient(path, {
            onStatus: (status, detail) => {
                this.dispatch("connection_status", {
                    status,
                    detail,
                });

                this.config.onConnectionStatus?.(status, detail);
            },
        });

        this.unsubscribeRealtime = [
            this.realtime.on(
                "notification.created",
                (notification) => this.handleCreated(notification)
            ),

            this.realtime.on(
                "notification.updated",
                (notification) => this.handleUpdated(notification)
            ),

            this.realtime.on(
                "notification.read",
                (notification) => this.handleRead(notification)
            ),

            this.realtime.on(
                "notification.unread",
                (notification) => this.handleUnread(notification)
            ),

            this.realtime.on(
                "notification.deleted",
                (notification) => this.handleDeleted(notification)
            ),
        ];

        this.realtime.connect();

        return this.realtime;
    }

    /**
     * Disconnect from real-time notifications.
     */
    static disconnectRealtime() {
        this.unsubscribeRealtime.forEach((unsubscribe) => unsubscribe());
        this.unsubscribeRealtime = [];

        this.realtime?.destroy();
        this.realtime = null;

        return this;
    }

    // ---------------------------------------------------------------------
    // Store operations
    // ---------------------------------------------------------------------

    /**
     * Return a stable identifier for a notification.
     */
    static getId(notification) {
        if (notification === null || notification === undefined) {
            return null;
        }

        if (typeof notification !== "object") {
            return notification;
        }

        return notification.id ?? notification.pk ?? null;
    }

    /**
     * Add or replace a notification in the store.
     */
    static update(notification) {
        const id = this.getId(notification);

        if (id === null || id === undefined || typeof notification !== "object") {
            return null;
        }

        const existing = this.notifications.get(id) || {};
        const updated = { ...existing, ...notification };

        this.notifications.set(id, updated);
        this.dispatch("updated", updated);

        return updated;
    }

    /**
     * Add or update multiple notifications.
     */
    static updateMany(notifications = []) {
        if (!Array.isArray(notifications)) {
            return [];
        }

        return notifications
            .map((notification) => this.update(notification))
            .filter(Boolean);
    }

    /**
     * Retrieve a notification by ID or notification object.
     */
    static get(id) {
        return this.notifications.get(this.getId(id)) ?? null;
    }

    /**
     * Check whether a notification is in the store.
     */
    static has(id) {
        return this.notifications.has(this.getId(id));
    }

    /**
     * Return all notifications, optionally sorted newest first.
     */
    static all({ sort = false } = {}) {
        const notifications = [...this.notifications.values()];

        if (sort) {
            notifications.sort((a, b) => {
                const dateA = new Date(
                    a.created_at ?? a.createdAt ?? 0
                ).getTime();

                const dateB = new Date(
                    b.created_at ?? b.createdAt ?? 0
                ).getTime();

                return dateB - dateA;
            });
        }

        return notifications;
    }

    /**
     * Return notifications that have not been read.
     *
     * Supports common Django field names: is_read and read_at.
     */
    static unread() {
        return this.all().filter((notification) => {
            if (typeof notification.is_read === "boolean") {
                return !notification.is_read;
            }

            if (typeof notification.read === "boolean") {
                return !notification.read;
            }

            if ("read_at" in notification) {
                return !notification.read_at;
            }

            // Unknown read state: don't incorrectly classify it as unread.
            return false;
        });
    }

    static unreadCount() {
        if (this.counts.unread !== null) {
            return this.counts.unread;
        }

        return this.unread().length;
    }

    static allCount() {
        if (this.counts.all !== null) {
            return this.counts.all;
        }

        return this.notifications.size;
    }

    /**
     * Remove a notification from the local store.
     */
    static remove(notification) {
        const id = this.getId(notification);

        if (id === null || id === undefined) {
            return false;
        }

        const removed = this.notifications.delete(id);

        if (removed) {
            this.dispatch("removed", { id });
        }

        return removed;
    }

    static clear() {
        this.notifications.clear();
        this.counts.unread = 0;
        this.counts.all = 0;

        this.dispatch("cleared", {});
        return this;
    }

    // ---------------------------------------------------------------------
    // Real-time event handlers
    // ---------------------------------------------------------------------

    static handleCreated(notification) {
        const updated = this.update(notification);

        if (!updated) return;

        this.incrementCountsForCreated(updated);

        this.dispatch("created", updated);
        this.emitDOMEvent("djangospice:notification_created", updated);
    }

    static handleUpdated(notification) {
        const updated = this.update(notification);

        if (!updated) return;

        this.refreshCachedUnreadCount();
        this.dispatch("notification_updated", updated);
    }

    static handleRead(notification) {
        const updated = this.updateReadState(notification, true);

        if (!updated) return;

        this.refreshCachedUnreadCount();

        this.dispatch("read", updated);
        this.emitDOMEvent("djangospice:notification_read", updated);
    }

    static handleUnread(notification) {
        const updated = this.updateReadState(notification, false);

        if (!updated) return;

        this.refreshCachedUnreadCount();

        this.dispatch("unread", updated);
        this.emitDOMEvent("djangospice:notification_unread", updated);
    }

    static handleDeleted(notification) {
        const id = this.getId(notification);
        const existing = this.get(id);

        if (id === null || id === undefined) return;

        this.remove(id);
        this.refreshCachedUnreadCount();

        this.dispatch("deleted", existing || notification);
        this.emitDOMEvent("djangospice:notification_deleted", {
            id,
        });
    }

    static updateReadState(notification, isRead) {
        const id = this.getId(notification);

        if (id === null || id === undefined) return null;

        const existing = this.get(id) || {};

        return this.update({
            ...existing,
            ...(typeof notification === "object" ? notification : {}),
            id,
            is_read: isRead,
        });
    }

    static incrementCountsForCreated(notification) {
        if (this.counts.all !== null) {
            this.counts.all += 1;
        }

        const isRead = notification.is_read === true ||
            notification.read === true;

        if (!isRead && this.counts.unread !== null) {
            this.counts.unread += 1;
        }
    }

    static refreshCachedUnreadCount() {
        if (this.counts.unread !== null) {
            this.counts.unread = this.unread().length;
        }
    }

    // ---------------------------------------------------------------------
    // HTTP API
    // ---------------------------------------------------------------------

    static async fetchUnread(options = {}) {
        const response = await this.request(
            this.config.endpoints.unreadList,
            { method: "GET", ...options }
        );

        const notifications = this.extractList(response);

        this.updateMany(notifications);
        this.counts.unread = notifications.length;

        return notifications;
    }

    static async fetchAll(options = {}) {
        const response = await this.request(
            this.config.endpoints.allList,
            { method: "GET", ...options }
        );

        const notifications = this.extractList(response);

        this.updateMany(notifications);

        if (Array.isArray(response)) {
            this.counts.all = response.length;
        } else if (typeof response?.count === "number") {
            this.counts.all = response.count;
        }

        return notifications;
    }

    static async fetchUnreadCount(options = {}) {
        const response = await this.request(
            this.config.endpoints.unreadCount,
            { method: "GET", ...options }
        );

        this.counts.unread = this.extractCount(response, "unread_count");

        return this.counts.unread;
    }

    static async fetchAllCount(options = {}) {
        const response = await this.request(
            this.config.endpoints.allCount,
            { method: "GET", ...options }
        );

        this.counts.all = this.extractCount(response, "count");

        return this.counts.all;
    }

    static async markRead(id, options = {}) {
        return this.mutateNotification(id, "read", options);
    }

    static async markUnread(id, options = {}) {
        return this.mutateNotification(id, "unread", options);
    }

    static async markAllRead(options = {}) {
        const response = await this.request(
            this.config.endpoints.markAllRead,
            {
                method: "POST",
                ...options,
            }
        );

        // Update known local notifications immediately.
        for (const notification of this.notifications.values()) {
            this.update({
                ...notification,
                is_read: true,
            });
        }

        this.counts.unread = 0;

        this.dispatch("all_read", {});
        return response;
    }

    static async delete(id, options = {}) {
        const notification = this.get(id);

        const response = await this.request(
            this.notificationEndpoint(id),
            {
                method: "DELETE",
                ...options,
            }
        );

        this.remove(id);
        this.refreshCachedUnreadCount();

        this.dispatch("deleted", notification || { id });

        return response;
    }

    static async mutateNotification(id, action, options = {}) {
        const endpoint = this.notificationEndpoint(id, action);

        const response = await this.request(endpoint, {
            method: "POST",
            ...options,
        });

        const isRead = action === "read";
        const updated = this.updateReadState({ id }, isRead);

        this.refreshCachedUnreadCount();

        this.dispatch(action, updated || { id });

        return response;
    }

    /**
     * Default per-notification endpoint convention:
     *   /notifications/api/<id>/read/
     *   /notifications/api/<id>/unread/
     *   /notifications/api/<id>/
     *
     * Override this method if your backend uses different URLs.
     */
    static notificationEndpoint(id, action = null) {
        const base = this.config.endpoints.allList.replace(/\/?$/, "/");
        const endpoint = `${base}${encodeURIComponent(id)}/`;

        return action ? `${endpoint}${action}/` : endpoint;
    }

    /**
     * Make a same-origin HTTP request and decode JSON responses.
     */
    static async request(url, options = {}) {
        const method = (options.method || "GET").toUpperCase();
        const headers = new Headers(options.headers || {});

        headers.set("Accept", "application/json");

        if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
            const csrfToken = this.getCSRFToken();

            if (csrfToken) {
                headers.set("X-CSRFToken", csrfToken);
            }

            if (
                options.body &&
                typeof options.body === "object" &&
                !(options.body instanceof FormData) &&
                !(options.body instanceof URLSearchParams)
            ) {
                headers.set("Content-Type", "application/json");
                options = {
                    ...options,
                    body: JSON.stringify(options.body),
                };
            }
        }

        const response = await fetch(url, {
            credentials: "same-origin",
            ...options,
            method,
            headers,
        });

        if (!response.ok) {
            const error = new Error(
                `Notification request failed: ${response.status} ${response.statusText}`
            );

            error.status = response.status;
            error.response = response;

            this.dispatch("request_error", {
                url,
                method,
                status: response.status,
            });

            throw error;
        }

        if (response.status === 204) {
            return null;
        }

        const contentType = response.headers.get("content-type") || "";

        return contentType.includes("application/json")
            ? response.json()
            : response.text();
    }

    static extractList(response) {
        if (Array.isArray(response)) return response;
        if (Array.isArray(response?.results)) return response.results;
        if (Array.isArray(response?.notifications)) return response.notifications;

        return [];
    }

    static extractCount(response, preferredKey) {
        if (typeof response === "number") return response;

        if (typeof response?.[preferredKey] === "number") {
            return response[preferredKey];
        }

        if (typeof response?.count === "number") {
            return response.count;
        }

        if (typeof response?.unread === "number") {
            return response.unread;
        }

        return 0;
    }

    static getCSRFToken() {
        const cookie = document.cookie
            .split("; ")
            .find((item) => item.startsWith("csrftoken="));

        if (cookie) {
            return decodeURIComponent(cookie.split("=").slice(1).join("="));
        }

        return document.querySelector(
            'meta[name="csrf-token"]'
        )?.content || "";
    }

    // ---------------------------------------------------------------------
    // Application events
    // ---------------------------------------------------------------------

    /**
     * Dispatch a namespaced browser event.
     *
     * Example:
     * document.addEventListener(
     *     "djangospice:notification:created",
     *     (event) => console.log(event.detail)
     * );
     */
    static dispatch(name, detail = {}) {
        document.dispatchEvent(
            new CustomEvent(`djangospice:notification:${name}`, {
                detail,
            })
        );
    }

    /**
     * Emit legacy DOM events for existing UI integrations.
     */
    static emitDOMEvent(name, notification) {
        document.dispatchEvent(
            new CustomEvent(name, {
                detail: { notification },
            })
        );
    }
}