
export class SocketListener {

    constructor(socket = globalThis.spice?.socket) {
        this.socket = socket;
        this.listeners = [];
    }

    listen(event, callback) {
        if (!this.socket) return this;
        
        if (this.listeners.some(
            item => item.event === event &&
                    item.callback === callback
        )) {
            return this;
        }

        this.socket.on(event, callback);

        this.listeners.push({
            event,
            callback,
        });

        return this;
    }

    destroy() {
        if (this.socket) {
            this.listeners.forEach(({ event, callback }) => {
                this.socket.off(event, callback);
            });
        }

        this.listeners = [];

        return this;
    }
}
