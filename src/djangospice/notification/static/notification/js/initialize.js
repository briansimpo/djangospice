/**
 * Initialize the notification system for the current application.
 *
 * Importing this module alone does not open a WebSocket.
 */
import { Notification } from "./notification.js";

export async function initializeNotifications(options = {}) {
    const {
        loadUnread = true,
        loadCounts = true,
        ...config
    } = options;

    Notification.configure(config);
    Notification.initialize();

    const requests = [];

    if (loadUnread) {
        requests.push(Notification.fetchUnread());
    }

    if (loadCounts) {
        requests.push(
            Notification.fetchUnreadCount(),
            Notification.fetchAllCount()
        );
    }

    const results = await Promise.allSettled(requests);

    return {
        Notification,
        results,
        realtime: Notification.realtime,
    };
}
