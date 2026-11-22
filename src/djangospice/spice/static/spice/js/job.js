
import { SocketListener } from "./listener.js";


export class JobListener extends SocketListener {

    initialize() {
        const body = document.body;

        const events = [
            "job_queued",
            "job_started",
            "job_progressed",
            "job_retrying",
            "job_completed",
            "job_failed",
        ];

        events.forEach(name => {
            this.listen(name, data => {
                const event = name.replaceAll("_", "-");

                // Specific lifecycle event.
                htmx.trigger(body, event, data);

                // General lifecycle event.
                htmx.trigger(body, "job-updated", {
                    ...data,
                    event: name,
                });
            });
        });

        return () => this.destroy();
    }
}


export async function initialize(socket=null) {
    return new JobListener(socket).initialize();
}
