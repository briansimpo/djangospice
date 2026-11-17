import { emit, ROUTER_EVENTS } from "../utils/config.js";

if (!customElements.get("spice-loading")) {
    customElements.define(
        "spice-loading",
        class extends HTMLElement {
            constructor() {
                super();
                this.requests = new Set();
                this.fallbackRequestCount = 0;
                this.onBeforeRequest = this.handleBeforeRequest.bind(this);
                this.onAfterRequest = this.handleAfterRequest.bind(this);
                this.onRequestError = this.handleRequestError.bind(this);
            }

            connectedCallback() {
                if (this.hasAttribute("data-initialized")) return;
                this.setAttribute("data-initialized", "true");
                this.style.display = "none";

                document.addEventListener("htmx:beforeRequest", this.onBeforeRequest);
                document.addEventListener("htmx:afterRequest", this.onAfterRequest);

                [
                    "htmx:sendError",
                    "htmx:timeout",
                    "htmx:sendAbort",
                    "htmx:responseError",
                ].forEach(event => {
                    document.addEventListener(event, this.onRequestError);
                });
            }

            disconnectedCallback() {
                document.removeEventListener("htmx:beforeRequest", this.onBeforeRequest);
                document.removeEventListener("htmx:afterRequest", this.onAfterRequest);

                [
                    "htmx:sendError",
                    "htmx:timeout",
                    "htmx:sendAbort",
                    "htmx:responseError",
                ].forEach(event => {
                    document.removeEventListener(event, this.onRequestError);
                });

                this.removeAttribute("data-initialized");
            }

            matchesRequest(detail) {
                const trigger = detail?.elt || detail?.requestConfig?.elt;
                const actualTarget = detail?.target;
                const scope = this.getAttribute("scope");
                const selector = this.getAttribute("target");

                if (scope && (!trigger || !trigger.closest(scope))) {
                    return false;
                }

                if (!selector) return true;

                try {
                    return Boolean(actualTarget?.matches(selector));
                } catch {
                    return false;
                }
            }

            getRequestKey(detail) {
                return detail?.xhr || null;
            }

            handleBeforeRequest(event) {
                const detail = event.detail || {};
                if (!this.matchesRequest(detail)) return;

                const key = this.getRequestKey(detail);
                if (key) {
                    this.requests.add(key);
                } else {
                    this.fallbackRequestCount++;
                }

                this.show();
            }

            handleAfterRequest(event) {
                const detail = event.detail || {};
                if (!this.matchesRequest(detail)) return;
                this.finishRequest(detail);
            }

            handleRequestError(event) {
                const detail = event.detail || {};
                if (!this.matchesRequest(detail)) return;
                this.finishRequest(detail);
            }

            finishRequest(detail) {
                const key = this.getRequestKey(detail);

                if (key) {
                    this.requests.delete(key);
                } else if (this.fallbackRequestCount > 0) {
                    this.fallbackRequestCount--;
                }

                if (this.requests.size === 0 && this.fallbackRequestCount === 0) {
                    this.hide();
                }
            }

            show() {
                this.style.display = "";
                this.classList.add("loading", "active");

                emit(this, ROUTER_EVENTS.LOADING, { element: this });
            }

            hide() {
                this.style.display = "none";
                this.classList.remove("loading", "active");

                emit(this, ROUTER_EVENTS.LOADED, { element: this });
            }
        }
    );
}