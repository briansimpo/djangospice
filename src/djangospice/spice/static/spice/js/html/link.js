import { resolveConfig, copyAttributes } from "../utils/config.js";

if (!customElements.get("spice-link")) {
    customElements.define(
        "spice-link",
        class extends HTMLElement {
            connectedCallback() {
                if (this.hasAttribute("data-initialized")) return;
                this.setAttribute("data-initialized", "true");

                const to = this.getAttribute("to") || "#";
                const anchor = document.createElement("a");
                anchor.href = to;

                copyAttributes(
                    this,
                    anchor,
                    new Set(["id", "to", "exact", "active-class", "match-query"])
                );

                anchor.dataset.spiceNavigation = "true";
                anchor.dataset.spiceLink = "true";

                if (this.hasAttribute("exact")) {
                    anchor.dataset.spiceExact = "true";
                }

                const activeClass = this.getAttribute("active-class");
                if (activeClass) {
                    anchor.dataset.spiceActiveClass = activeClass;
                }

                if (this.hasAttribute("match-query")) {
                    anchor.dataset.spiceMatchQuery = "true";
                }

                while (this.firstChild) {
                    anchor.appendChild(this.firstChild);
                }

                this.appendChild(anchor);

                const config = resolveConfig(this);
                anchor.setAttribute("hx-get", to);
                anchor.setAttribute("hx-target", config.target);
                anchor.setAttribute("hx-select", config.select);

                const swap = config.transition
                    ? `${config.swap} transition:true`
                    : config.swap;

                anchor.setAttribute("hx-swap", swap);
                anchor.setAttribute("hx-push-url", config.pushUrl ? "true" : "false");

                if (config.preload) {
                    anchor.setAttribute("preload", "mouseover");
                }

                anchor.dataset.spiceRouterProcessed = "true";

                if (window.htmx) {
                    window.htmx.process(anchor);
                }
            }
        }
    );
}