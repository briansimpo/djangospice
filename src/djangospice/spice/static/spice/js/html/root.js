if (!customElements.get("spice-app")) {
    customElements.define(
        "spice-app",
        class extends HTMLElement {
            connectedCallback() {
                this.dispatchEvent(
                    new CustomEvent("spice:app:connected", {
                        bubbles: true,
                        composed: true,
                        detail: { element: this },
                    })
                );
            }
        }
    );
}