
import { normalizePath, ROUTER_EVENTS, emit } from "./utils/config.js";


export class SpiceRouter {
    constructor(options = {}) {
        this.options = options;
        this.started = false;
        this.observer = null;

        this.boundHandlers = {
            beforeRequest: this.handleBeforeRequest.bind(this),
            beforeSwap: this.handleBeforeSwap.bind(this),
            afterSwap: this.handleAfterSwap.bind(this),
            afterRequest: this.handleAfterRequest.bind(this),
            pushedIntoHistory: this.handlePushedIntoHistory.bind(this),
            requestError: this.handleRequestError.bind(this),
            popstate: this.handlePopState.bind(this),
        };
    }

    start() {
        if (this.started) {
            this.processDocument();
            return this;
        }

        this.initListeners();
        this.observeDOM();
        this.started = true;

        this.processDocument();

        emit(document, ROUTER_EVENTS.READY, { router: this });
        return this;
    }

    stop() {
        if (!this.started) return this;

        document.removeEventListener("htmx:beforeRequest", this.boundHandlers.beforeRequest);
        document.removeEventListener("htmx:beforeSwap", this.boundHandlers.beforeSwap);
        document.removeEventListener("htmx:afterSwap", this.boundHandlers.afterSwap);
        document.removeEventListener("htmx:afterRequest", this.boundHandlers.afterRequest);
        document.removeEventListener("htmx:pushedIntoHistory", this.boundHandlers.pushedIntoHistory);
        document.removeEventListener("htmx:responseError", this.boundHandlers.requestError);
        document.removeEventListener("htmx:sendError", this.boundHandlers.requestError);
        document.removeEventListener("htmx:timeout", this.boundHandlers.requestError);
        document.removeEventListener("htmx:sendAbort", this.boundHandlers.requestError);

        window.removeEventListener("popstate", this.boundHandlers.popstate);

        this.observer?.disconnect();
        this.observer = null;
        this.started = false;

        return this;
    }

    updateOptions(options = {}) {
        this.options = { ...this.options, ...options };
        this.refreshActiveLinks();
        return this;
    }

    processDocument() {
        this.refreshActiveLinks();
    }

    refreshActiveLinks() {
        const currentURL = new URL(window.location.href);
        const currentPath = normalizePath(currentURL.pathname);

        document.querySelectorAll("a[data-spice-link]").forEach(anchor => {
            let active = false;

            try {
                const linkURL = new URL(anchor.href, window.location.href);
                const linkPath = normalizePath(linkURL.pathname);

                const exact = anchor.dataset.spiceExact === "true";
                const matchQuery = anchor.dataset.spiceMatchQuery === "true";

                if (exact) {
                    active = linkPath === currentPath;
                } else {
                    active =
                        linkPath === "/" ||
                        linkPath === currentPath ||
                        currentPath.startsWith(`${linkPath}/`);
                }

                if (active && matchQuery && linkURL.search !== currentURL.search) {
                    active = false;
                }
            } catch {
                active = false;
            }

            const activeClass = anchor.dataset.spiceActiveClass || "active";
            anchor.classList.toggle(activeClass, active);

            if (active) {
                anchor.setAttribute("aria-current", "page");
            } else {
                anchor.removeAttribute("aria-current");
            }
        });
    }

    initListeners() {
        document.addEventListener("htmx:beforeRequest", this.boundHandlers.beforeRequest);
        document.addEventListener("htmx:beforeSwap", this.boundHandlers.beforeSwap);
        document.addEventListener("htmx:afterSwap", this.boundHandlers.afterSwap);
        document.addEventListener("htmx:afterRequest", this.boundHandlers.afterRequest);
        document.addEventListener("htmx:pushedIntoHistory", this.boundHandlers.pushedIntoHistory);
        document.addEventListener("htmx:responseError", this.boundHandlers.requestError);
        document.addEventListener("htmx:sendError", this.boundHandlers.requestError);
        document.addEventListener("htmx:timeout", this.boundHandlers.requestError);
        document.addEventListener("htmx:sendAbort", this.boundHandlers.requestError);

        window.addEventListener("popstate", this.boundHandlers.popstate);
    }

    getTriggerElement(detail) {
        return detail?.requestConfig?.elt || detail?.elt || null;
    }

    isRouterRequest(detail) {
        const element = this.getTriggerElement(detail);
        return Boolean(element?.matches?.("[data-spice-navigation]"));
    }

    handleBeforeRequest(event) {
        const detail = event.detail || {};
        if (!this.isRouterRequest(detail)) return;

        const element = this.getTriggerElement(detail);
        const beforeEvent = emit(
            element,
            ROUTER_EVENTS.BEFORE_NAVIGATE,
            { element, target: detail.target, xhr: detail.xhr, requestConfig: detail.requestConfig },
            { cancelable: true }
        );

        if (beforeEvent.defaultPrevented) {
            event.preventDefault();
        }
    }

    handleBeforeSwap(event) {
        const detail = event.detail || {};
        if (!this.isRouterRequest(detail)) return;

        const element = this.getTriggerElement(detail);
        const beforeEvent = emit(
            element,
            ROUTER_EVENTS.BEFORE_SWAP,
            { element, target: detail.target, xhr: detail.xhr, requestConfig: detail.requestConfig },
            { cancelable: true }
        );

        if (beforeEvent.defaultPrevented) {
            event.preventDefault();
        }
    }

    handleAfterSwap(event) {
        const detail = event.detail || {};
        if (!this.isRouterRequest(detail)) return;

        const element = this.getTriggerElement(detail);
        const target = detail.target || event.target;

        emit(target, ROUTER_EVENTS.AFTER_SWAP, { element, target, xhr: detail.xhr });
        emit(target, ROUTER_EVENTS.NAVIGATE, { element, target, url: window.location.href, xhr: detail.xhr });

        this.refreshActiveLinks();
    }

    handleAfterRequest(event) {
        const detail = event.detail || {};
        if (!this.isRouterRequest(detail)) return;

        if (detail.failed) {
            this.emitNavigationError(detail);
        }
    }

    handleRequestError(event) {
        const detail = event.detail || {};
        if (!this.isRouterRequest(detail)) return;

        this.emitNavigationError(detail);
    }

    emitNavigationError(detail) {
        const element = this.getTriggerElement(detail);
        emit(element, ROUTER_EVENTS.NAVIGATION_ERROR, {
            element,
            xhr: detail.xhr,
            status: detail.xhr?.status,
            error: detail.error,
            failed: detail.failed,
        });
    }

    handlePushedIntoHistory(event) {
        this.refreshActiveLinks();
        emit(document, ROUTER_EVENTS.LOCATION_CHANGE, {
            url: window.location.href,
            source: "htmx",
            detail: event.detail,
        });
    }

    handlePopState() {
        this.refreshActiveLinks();
        emit(document, ROUTER_EVENTS.LOCATION_CHANGE, {
            url: window.location.href,
            source: "popstate",
        });
    }

    observeDOM() {
        if (this.observer || !document.body) return;

        this.observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (window.htmx) {
                                window.htmx.process(node);
                            }
                        }
                    }
                }
            }
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }
}