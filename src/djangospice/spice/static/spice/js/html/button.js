import { resolveConfig, copyAttributes, HTTP_METHODS, parseBoolean } from "../utils/config.js";

if (!customElements.get("spice-button")) {
    customElements.define(
        "spice-button",
        class extends HTMLElement {
            connectedCallback() {
                if (this.hasAttribute("data-initialized")) return;
                this.setAttribute("data-initialized", "true");

                const to = this.getAttribute("to");
                const method = (this.getAttribute("method") || "get").toLowerCase();

                if (!to || !HTTP_METHODS.has(method)) {
                    console.error("SpiceButton: Invalid configuration.", this);
                    return;
                }

                const button = document.createElement("button");
                button.type = this.getAttribute("type") || "button";

                copyAttributes(this, button, new Set(["id", "to", "method", "push-url"]));
                button.dataset.spiceNavigation = "true";

                while (this.firstChild) {
                    button.appendChild(this.firstChild);
                }

                this.appendChild(button);

                const config = resolveConfig(this);
                const effectivePushUrl = parseBoolean(
                    this.getAttribute("push-url"),
                    method === "get"
                );

                button.setAttribute(`hx-${method}`, to);
                button.setAttribute("hx-target", config.target);
                button.setAttribute("hx-select", config.select);

                const swap = config.transition
                    ? `${config.swap} transition:true`
                    : config.swap;

                button.setAttribute("hx-swap", swap);

                if (method === "get") {
                    button.setAttribute("hx-push-url", effectivePushUrl ? "true" : "false");
                } else if (effectivePushUrl) {
                    button.setAttribute("hx-push-url", "true");
                }

                button.dataset.spiceRouterProcessed = "true";

                if (window.htmx) {
                    window.htmx.process(button);
                }
            }
        }
    );
}