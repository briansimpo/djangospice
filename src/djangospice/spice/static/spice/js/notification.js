import { SocketListener } from "./listener.js";


export class NotificationListener extends SocketListener {

    initialize() {
        const body = document.body;

        this.listen("notification_created", () => {
            htmx.trigger(body, "refresh-notifications");
        });

        this.listen("notification_read", () => {
            htmx.trigger(body, "refresh-notifications");
        });

        this.listen("notification_read_all", () => {
            htmx.trigger(body, "refresh-notifications");
        });

        return () => this.destroy();
    }
}


export async function initialize(socket=null) {
    return new NotificationListener(socket).initialize();
}