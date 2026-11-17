import { resolveConfig, shouldEnhanceAnchor } from "../utils/config.js";

if (!customElements.get("spice-nav")) {
    customElements.define(
        "spice-nav",
        class extends HTMLElement {
            connectedCallback() {
                this.querySelectorAll("a[href]").forEach(anchor => {
                    if (anchor.dataset.spiceRouterProcessed === "true") return;
                    if (!shouldEnhanceAnchor(anchor)) return;

                    const to = anchor.getAttribute("href");
                    const config = resolveConfig(anchor);

                    anchor.setAttribute("hx-get", to);
                    anchor.setAttribute("hx-target", config.target);
                    anchor.setAttribute("hx-select", config.select);
                    anchor.setAttribute("hx-swap", config.transition ? `${config.swap} transition:true` : config.swap);
                    anchor.setAttribute("hx-push-url", config.pushUrl ? "true" : "false");

                    anchor.dataset.spiceNavigation = "true";
                    anchor.dataset.spiceLink = "true";
                    anchor.dataset.spiceRouterProcessed = "true";

                    if (window.htmx) {
                        window.htmx.process(anchor);
                    }
                });
            }
        }
    );
}