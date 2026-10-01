/**
 * Djangospice Notification Client
 *
 * Client-side notification state manager and HTTP API client.
 *
 * Responsibilities:
 * - Maintain notification state in memory.
 * - Consume notification realtime events.
 * - Fetch notifications from the server.
 * - Perform notification mutations through server-provided URLs.
 *
 * The server remains the source of truth.
 *
 * Realtime events:
 * - djangospice:notification_created
 * - djangospice:notification_read
 * - djangospice:notification_unread
 * - djangospice:notification_deleted
 */

export class Notification {
    static notifications = new Map();

    static initialized = false;

    static endpoints = {
        unreadList: null,
        allList: null,
        unreadCount: null,
        allCount: null,
        markAllRead: null,
    };

    /**
     * Configure notification API endpoints.
     *
     * Individual notification mutation URLs are not configured here.
     * They are provided by the server in notification.urls.
     *
     * @param {Object} options
     * @param {Object} options.endpoints
     */
    static configure(options = {}) {
        this.endpoints = {
            ...this.endpoints,
            ...(options.endpoints || {}),
        };
    }

    /**
     * Initialize realtime notification listeners.
     *
     * Safe to call multiple times.
     */
    static initialize() {
        if (this.initialized) {
            return;
        }

        this.initialized = true;

        document.addEventListener(
            "djangospice:notification_created",
            (event) => {
                this.update(
                    event.detail?.notification,
                );
            },
        );

        document.addEventListener(
            "djangospice:notification_read",
            (event) => {
                this.update(
                    event.detail?.notification,
                );
            },
        );

        document.addEventListener(
            "djangospice:notification_unread",
            (event) => {
                this.update(
                    event.detail?.notification,
                );
            },
        );

        document.addEventListener(
            "djangospice:notification_deleted",
            (event) => {
                this.remove(
                    event.detail?.notification,
                );
            },
        );
    }

    /**
     * Add or update a notification in the local state.
     *
     * @param {Object} notification
     * @returns {Object|null}
     */
    static update(notification) {
        if (!notification?.id) {
            return null;
        }

        const current = this.notifications.get(
            notification.id,
        );

        const updated = {
            ...current,
            ...notification,
        };

        this.notifications.set(
            notification.id,
            updated,
        );

        return updated;
    }

    /**
     * Add or update multiple notifications.
     *
     * @param {Array<Object>} notifications
     * @returns {Array<Object>}
     */
    static updateMany(notifications = []) {
        for (const notification of notifications) {
            this.update(notification);
        }

        return this.all();
    }

    /**
     * Get a notification by ID.
     *
     * @param {string} id
     * @returns {Object|undefined}
     */
    static get(id) {
        return this.notifications.get(id);
    }

    /**
     * Check whether a notification exists locally.
     *
     * @param {string} id
     * @returns {boolean}
     */
    static has(id) {
        return this.notifications.has(id);
    }

    /**
     * Return all locally known notifications.
     *
     * @returns {Array<Object>}
     */
    static all() {
        return Array.from(
            this.notifications.values(),
        );
    }

    /**
     * Return locally known unread notifications.
     *
     * @returns {Array<Object>}
     */
    static unread() {
        return this.all().filter(
            (notification) => notification.unread === true,
        );
    }

    /**
     * Return the locally known unread count.
     *
     * @returns {number}
     */
    static unreadCount() {
        return this.unread().length;
    }

    /**
     * Remove a notification from local state.
     *
     * Accepts either a notification object or an ID.
     *
     * @param {Object|string} notification
     */
    static remove(notification) {
        const id =
            typeof notification === "string"
                ? notification
                : notification?.id;

        if (!id) {
            return;
        }

        this.notifications.delete(id);
    }

    /**
     * Clear all local notification state.
     */
    static clear() {
        this.notifications.clear();
    }

    /**
     * Fetch unread notifications from the server.
     *
     * @returns {Promise<Object>}
     */
    static async fetchUnread() {
        const response = await this.request(
            this.endpoints.unreadList,
        );

        this.updateMany(
            response.unread_list || [],
        );

        return response;
    }

    /**
     * Fetch all notifications from the server.
     *
     * @returns {Promise<Object>}
     */
    static async fetchAll() {
        const response = await this.request(
            this.endpoints.allList,
        );

        this.updateMany(
            response.all_list || [],
        );

        return response;
    }

    /**
     * Fetch the unread notification count.
     *
     * @returns {Promise<number>}
     */
    static async fetchUnreadCount() {
        const response = await this.request(
            this.endpoints.unreadCount,
        );

        return response.unread_count ?? 0;
    }

    /**
     * Fetch the total notification count.
     *
     * @returns {Promise<number>}
     */
    static async fetchAllCount() {
        const response = await this.request(
            this.endpoints.allCount,
        );

        return response.all_count ?? 0;
    }

    /**
     * Mark a notification as read.
     *
     * The mutation URL comes from notification.urls.read.
     *
     * @param {Object} notification
     * @returns {Promise<Object>}
     */
    static async markRead(notification) {
        const response = await this.request(
            notification?.urls?.read,
            {
                method: "POST",
            },
        );

        if (response.notification) {
            this.update(response.notification);
        }

        return response;
    }

    /**
     * Mark a notification as unread.
     *
     * The mutation URL comes from notification.urls.unread.
     *
     * @param {Object} notification
     * @returns {Promise<Object>}
     */
    static async markUnread(notification) {
        const response = await this.request(
            notification?.urls?.unread,
            {
                method: "POST",
            },
        );

        if (response.notification) {
            this.update(response.notification);
        }

        return response;
    }

    /**
     * Mark all notifications as read.
     *
     * @returns {Promise<Object>}
     */
    static async markAllRead() {
        const response = await this.request(
            this.endpoints.markAllRead,
            {
                method: "POST",
            },
        );

        /*
         * The server returns the authoritative unread count.
         * Individual notification state will also be synchronized
         * through notification_read realtime events.
         */
        return response;
    }

    /**
     * Delete a notification.
     *
     * The mutation URL comes from notification.urls.delete.
     *
     * @param {Object} notification
     * @returns {Promise<Object>}
     */
    static async delete(notification) {
        const response = await this.request(
            notification?.urls?.delete,
            {
                method: "POST",
            },
        );

        /*
         * Remove immediately from local state after a
         * successful server response. The realtime event
         * provides the authoritative synchronization path.
         */
        if (response.deleted && response.id) {
            this.remove(response.id);
        }

        return response;
    }

    /**
     * Execute an HTTP request against the notification API.
     *
     * @param {string} url
     * @param {Object} options
     * @returns {Promise<Object>}
     */
    static async request(url, options = {}) {
        if (!url) {
            throw new Error(
                "Djangospice: notification endpoint is not configured.",
            );
        }

        const method = (
            options.method || "GET"
        ).toUpperCase();

        const headers = {
            Accept: "application/json",
            ...options.headers,
        };

        if (
            method !== "GET" &&
            method !== "HEAD" &&
            method !== "OPTIONS"
        ) {
            const csrfToken = this.getCSRFToken();

            if (csrfToken) {
                headers["X-CSRFToken"] = csrfToken;
            }
        }

        const response = await fetch(
            url,
            {
                credentials: "same-origin",
                ...options,
                method,
                headers,
            },
        );

        if (!response.ok) {
            throw new Error(
                `Djangospice: notification request failed: ${response.status}`,
            );
        }

        const contentType =
            response.headers.get("content-type") || "";

        if (
            contentType.includes(
                "application/json",
            )
        ) {
            return response.json();
        }

        return {
            response,
        };
    }

    /**
     * Read Django's CSRF token from the csrftoken cookie.
     *
     * @returns {string|null}
     */
    static getCSRFToken() {
        const name = "csrftoken=";

        const cookies = document.cookie
            .split(";")
            .map((cookie) => cookie.trim());

        for (const cookie of cookies) {
            if (cookie.startsWith(name)) {
                return decodeURIComponent(
                    cookie.slice(name.length),
                );
            }
        }

        return null;
    }
}