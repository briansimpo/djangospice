
/**
 * SpiceRouter
 *
 * Framework-agnostic navigation layer built on HTMX.
 *
 * Public elements:
 *   <spice-app>
 *   <spice-link>
 *   <spice-button>
 *   <spice-nav>
 *   <spice-boost>
 *   <spice-loading>
 *
 * HTMX owns:
 *   - HTTP requests
 *   - DOM swapping
 *   - Browser history
 *
 * SpiceRouter owns:
 *   - Navigation configuration
 *   - Custom navigation elements
 *   - Active navigation links
 *   - Loading indicators
 *   - Navigation lifecycle events
 *   - Dynamic navigation enhancement
 */

const DEFAULTS = {
    target: "spice-app",
    select: "spice-app",
    swap: "innerHTML show:window:top",
    transition: false,
    preload: false,
    pushUrl: true,
};

const HTTP_METHODS = new Set([
    "get", "post", "put", "patch", "delete",
]);

const RESERVED_ATTRIBUTES = new Set([
    "to",
    "method",
    "exact",
    "active-class",
    "match-query",
    "transition",
    "preload",
    "push-url",
    "select",
    "swap",
    "target",
    "data-initialized",
]);

const CONTAINER_SELECTOR = [
    "spice-app",
    "spice-nav",
    "spice-boost",
    "[spice-boost]",
].join(",");

const ROUTER_EVENTS = {
    READY: "spice:router:ready",
    BEFORE_NAVIGATE: "spice:router:before-navigate",
    BEFORE_SWAP: "spice:router:before-swap",
    AFTER_SWAP: "spice:router:after-swap",
    NAVIGATE: "spice:router:navigate",
    LOCATION_CHANGE: "spice:router:location-change",
    NAVIGATION_ERROR: "spice:router:navigation-error",
    LOADING: "spice:router:loading",
    LOADED: "spice:router:loaded",
};


/* -------------------------------------------------------------------------- */
/* Utilities                                                                  */
/* -------------------------------------------------------------------------- */

function emit(target, name, detail = {}, options = {}) {
    return (target || document).dispatchEvent(
        new CustomEvent(name, {
            bubbles: true,
            composed: true,
            cancelable: options.cancelable ?? false,
            detail,
        })
    );
}


function parseBoolean(value, fallback = false) {
    if (value === null || value === undefined) return fallback;
    if (value === "") return true;

    return !["false", "0", "off", "no"].includes(
        String(value).toLowerCase()
    );
}


function normalizePath(path) {
    if (!path) return "/";

    let result = path.replace(/\/+/g, "/");

    if (result.length > 1) {
        result = result.replace(/\/$/, "");
    }

    return result || "/";
}


function isInternalURL(value) {
    if (!value) return false;

    try {
        const url = new URL(value, window.location.href);

        return (
            ["http:", "https:"].includes(url.protocol) &&
            url.origin === window.location.origin
        );
    } catch {
        return false;
    }
}


function shouldEnhanceAnchor(anchor) {
    if (!anchor?.hasAttribute("href")) return false;

    const href = anchor.getAttribute("href");

    if (!href || href.startsWith("#")) return false;

    try {
        const url = new URL(href, window.location.href);

        // Ignore links to fragments on the current page.
        if (
            url.origin === window.location.origin &&
            url.pathname === window.location.pathname &&
            url.search === window.location.search &&
            url.hash
        ) {
            return false;
        }
    } catch {
        return false;
    }

    if (!isInternalURL(anchor.href)) return false;

    if (
        anchor.hasAttribute("download") ||
        anchor.target === "_blank" ||
        anchor.relList.contains("external") ||
        anchor.getAttribute("hx-boost") === "false"
    ) {
        return false;
    }

    return true;
}


function copyAttributes(source, destination, excluded = new Set()) {
    for (const attribute of source.attributes) {
        const name = attribute.name;

        if (
            RESERVED_ATTRIBUTES.has(name) ||
            excluded.has(name) ||
            name.startsWith("data-spice-internal-")
        ) {
            continue;
        }

        destination.setAttribute(name, attribute.value);
    }
}


/* -------------------------------------------------------------------------- */
/* SpiceRouter                                                                */
/* -------------------------------------------------------------------------- */

export class SpiceRouter {

    constructor(options = {}) {
        this.options = {
            ...DEFAULTS,
            ...options,
        };

        this.started = false;
        this.apps = new Set();
        this.observer = null;

        this.boundHandlers = {
            beforeRequest: this.handleBeforeRequest.bind(this),
            beforeSwap: this.handleBeforeSwap.bind(this),
            afterSwap: this.handleAfterSwap.bind(this),
            afterRequest: this.handleAfterRequest.bind(this),
            pushedIntoHistory: this.handlePushedIntoHistory.bind(this),

            responseError: this.handleRequestError.bind(this),
            sendError: this.handleRequestError.bind(this),
            timeout: this.handleRequestError.bind(this),
            sendAbort: this.handleRequestError.bind(this),

            popstate: this.handlePopState.bind(this),
        };
    }


    /* ---------------------------------------------------------------------- */
    /* Lifecycle                                                              */
    /* ---------------------------------------------------------------------- */

    start() {
        if (this.started) {
            this.processDocument();
            return this;
        }

        // Custom elements are registered independently of HTMX.
        this.registerElements();

        this.initListeners();
        this.observeDOM();

        this.started = true;

        // If HTMX is already available, process existing content.
        this.processDocument();

        emit(document, ROUTER_EVENTS.READY, {
            router: this,
        });

        return this;
    }


    stop() {
        if (!this.started) return this;

        const events = {
            "htmx:beforeRequest": "beforeRequest",
            "htmx:beforeSwap": "beforeSwap",
            "htmx:afterSwap": "afterSwap",
            "htmx:afterRequest": "afterRequest",
            "htmx:pushedIntoHistory": "pushedIntoHistory",
            "htmx:responseError": "responseError",
            "htmx:sendError": "sendError",
            "htmx:timeout": "timeout",
            "htmx:sendAbort": "sendAbort",
        };

        for (const [event, handler] of Object.entries(events)) {
            document.removeEventListener(
                event,
                this.boundHandlers[handler]
            );
        }

        window.removeEventListener(
            "popstate",
            this.boundHandlers.popstate
        );

        this.observer?.disconnect();
        this.observer = null;

        this.started = false;

        return this;
    }


    updateOptions(options = {}) {
        this.options = {
            ...this.options,
            ...options,
        };

        this.processExistingContainers();
        this.refreshActiveLinks();

        return this;
    }


    /* ---------------------------------------------------------------------- */
    /* Custom elements                                                        */
    /* ---------------------------------------------------------------------- */

    registerElements() {
        const router = this;

        // spice-app

        if (!customElements.get("spice-app")) {
            customElements.define(
                "spice-app",
                class extends HTMLElement {

                    connectedCallback() {
                        router.apps.add(this);
                    }

                    disconnectedCallback() {
                        router.apps.delete(this);
                    }
                }
            );
        }


        // spice-link

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
                            new Set(["id"])
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

                        // Initialize after appending so inherited container
                        // configuration can be resolved correctly.
                        router.initializeRequest(anchor, {
                            to,
                            method: "get",
                        });

                        router.refreshActiveLinks();
                    }
                }
            );
        }


        // spice-button

        if (!customElements.get("spice-button")) {
            customElements.define(
                "spice-button",
                class extends HTMLElement {

                    connectedCallback() {
                        if (this.hasAttribute("data-initialized")) return;

                        this.setAttribute("data-initialized", "true");

                        const to = this.getAttribute("to");
                        const method = (
                            this.getAttribute("method") || "get"
                        ).toLowerCase();

                        if (!to || !HTTP_METHODS.has(method)) {
                            console.error(
                                "SpiceRouter: Invalid spice-button configuration.",
                                this
                            );
                            return;
                        }

                        const button = document.createElement("button");

                        button.type = this.getAttribute("type") || "button";

                        copyAttributes(
                            this,
                            button,
                            new Set(["id"])
                        );

                        button.dataset.spiceNavigation = "true";

                        while (this.firstChild) {
                            button.appendChild(this.firstChild);
                        }

                        this.appendChild(button);

                        router.initializeRequest(button, {
                            to,
                            method,
                            pushUrl: parseBoolean(
                                this.getAttribute("push-url"),
                                method === "get"
                            ),
                        });
                    }
                }
            );
        }


        // spice-nav

        if (!customElements.get("spice-nav")) {
            customElements.define(
                "spice-nav",
                class extends HTMLElement {

                    connectedCallback() {
                        router.processBoostContainer(this);
                    }
                }
            );
        }


        // spice-boost

        if (!customElements.get("spice-boost")) {
            customElements.define(
                "spice-boost",
                class extends HTMLElement {

                    connectedCallback() {
                        router.processBoostContainer(this);
                    }
                }
            );
        }


        // spice-loading

        if (!customElements.get("spice-loading")) {
            customElements.define(
                "spice-loading",
                class extends HTMLElement {

                    constructor() {
                        super();

                        this.requests = new Set();
                        this.fallbackRequestCount = 0;

                        this.onBeforeRequest =
                            this.handleBeforeRequest.bind(this);

                        this.onAfterRequest =
                            this.handleAfterRequest.bind(this);

                        this.onRequestError =
                            this.handleRequestError.bind(this);
                    }


                    connectedCallback() {
                        if (this.hasAttribute("data-initialized")) return;

                        this.setAttribute("data-initialized", "true");
                        this.style.display = "none";

                        document.addEventListener(
                            "htmx:beforeRequest",
                            this.onBeforeRequest
                        );

                        document.addEventListener(
                            "htmx:afterRequest",
                            this.onAfterRequest
                        );

                        [
                            "htmx:sendError",
                            "htmx:timeout",
                            "htmx:sendAbort",
                            "htmx:responseError",
                        ].forEach(event => {
                            document.addEventListener(
                                event,
                                this.onRequestError
                            );
                        });
                    }


                    disconnectedCallback() {
                        document.removeEventListener(
                            "htmx:beforeRequest",
                            this.onBeforeRequest
                        );

                        document.removeEventListener(
                            "htmx:afterRequest",
                            this.onAfterRequest
                        );

                        [
                            "htmx:sendError",
                            "htmx:timeout",
                            "htmx:sendAbort",
                            "htmx:responseError",
                        ].forEach(event => {
                            document.removeEventListener(
                                event,
                                this.onRequestError
                            );
                        });

                        this.removeAttribute("data-initialized");
                    }


                    matchesRequest(detail) {
                        const trigger =
                            detail?.elt ||
                            detail?.requestConfig?.elt;

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

                        if (
                            this.requests.size === 0 &&
                            this.fallbackRequestCount === 0
                        ) {
                            this.hide();
                        }
                    }


                    show() {
                        this.style.display = "";
                        this.classList.add("loading", "active");

                        emit(this, ROUTER_EVENTS.LOADING, {
                            element: this,
                        });
                    }


                    hide() {
                        this.style.display = "none";
                        this.classList.remove("loading", "active");

                        emit(this, ROUTER_EVENTS.LOADED, {
                            element: this,
                        });
                    }
                }
            );
        }
    }


    /* ---------------------------------------------------------------------- */
    /* Configuration                                                          */
    /* ---------------------------------------------------------------------- */

    resolveConfig(element) {
        const config = {
            ...this.options,
        };

        const containers = [];
        let current = element;

        while (current && current !== document.documentElement) {
            if (current.matches?.(CONTAINER_SELECTOR)) {
                containers.push(current);
            }

            current = current.parentElement;
        }

        containers.reverse();

        const apply = (source, isRequestElement = false) => {
            if (!source?.getAttribute) return;

            const target = source.getAttribute(
                isRequestElement ? "hx-target" : "target"
            );

            const select = source.getAttribute("select");
            const swap = source.getAttribute("swap");

            const transition = source.getAttribute("transition");
            const preload = source.getAttribute("preload");
            const pushUrl = source.getAttribute("push-url");

            if (target !== null) config.target = target;
            if (select !== null) config.select = select;
            if (swap !== null) config.swap = swap;

            if (transition !== null) {
                config.transition = parseBoolean(
                    transition,
                    config.transition
                );
            }

            if (preload !== null) {
                config.preload = parseBoolean(
                    preload,
                    config.preload
                );
            }

            if (pushUrl !== null) {
                config.pushUrl = parseBoolean(
                    pushUrl,
                    config.pushUrl
                );
            }
        };

        containers.forEach(container => apply(container));
        apply(element, true);

        config.target ||= "spice-app";
        config.select ||= config.target;
        config.swap ||= DEFAULTS.swap;

        return config;
    }


    /* ---------------------------------------------------------------------- */
    /* Request initialization                                                 */
    /* ---------------------------------------------------------------------- */

    initializeRequest(element, {
        to,
        method = "get",
        pushUrl,
    } = {}) {
        if (!element || !to) return false;

        method = method.toLowerCase();

        if (!HTTP_METHODS.has(method)) {
            console.error(`SpiceRouter: Unsupported method "${method}".`);
            return false;
        }

        if (!isInternalURL(to)) return false;

        const config = this.resolveConfig(element);

        const effectivePushUrl =
            pushUrl ?? (method === "get" && config.pushUrl);

        element.setAttribute(`hx-${method}`, to);
        element.setAttribute("hx-target", config.target);
        element.setAttribute("hx-select", config.select);

        const swap = config.transition
            ? `${config.swap} transition:true`
            : config.swap;

        element.setAttribute("hx-swap", swap);

        if (method === "get") {
            element.setAttribute(
                "hx-push-url",
                effectivePushUrl ? "true" : "false"
            );
        } else if (effectivePushUrl) {
            element.setAttribute("hx-push-url", "true");
        }

        element.dataset.spiceNavigation = "true";
        element.dataset.spiceRouterProcessed = "true";

        if (config.preload) {
            element.setAttribute("preload", "mouseover");
        }

        // Attributes are always applied, even if HTMX is not loaded yet.
        if (window.htmx) {
            window.htmx.process(element);
        }

        return true;
    }


    /* ---------------------------------------------------------------------- */
    /* Boost containers                                                       */
    /* ---------------------------------------------------------------------- */

    processBoostContainer(container) {
        if (!container) return;

        container.querySelectorAll("a[href]").forEach(anchor => {
            if (anchor.dataset.spiceRouterProcessed === "true") return;
            if (!shouldEnhanceAnchor(anchor)) return;

            const to = anchor.getAttribute("href");

            if (this.initializeRequest(anchor, {
                to,
                method: "get",
            })) {
                anchor.dataset.spiceLink = "true";
            }
        });

        container.querySelectorAll(
            "button[hx-get], button[hx-post], button[hx-put], button[hx-patch], button[hx-delete]"
        ).forEach(button => {
            if (button.dataset.spiceRouterProcessed === "true") return;

            const config = this.resolveConfig(button);

            button.setAttribute("hx-target", config.target);
            button.setAttribute("hx-select", config.select);

            if (!button.hasAttribute("hx-swap")) {
                button.setAttribute(
                    "hx-swap",
                    config.transition
                        ? `${config.swap} transition:true`
                        : config.swap
                );
            }

            button.dataset.spiceNavigation = "true";
            button.dataset.spiceRouterProcessed = "true";

            if (window.htmx) {
                window.htmx.process(button);
            }
        });
    }


    initBoostContainers(root = document) {
        if (root.nodeType !== Node.ELEMENT_NODE &&
            root.nodeType !== Node.DOCUMENT_NODE) {
            return;
        }

        // Include the root itself when it is a boost container.
        if (root.matches?.(CONTAINER_SELECTOR)) {
            this.processBoostContainer(root);
        }

        root.querySelectorAll?.(CONTAINER_SELECTOR).forEach(container => {
            this.processBoostContainer(container);
        });
    }


    processDocument() {
        if (document.body) {
            this.initBoostContainers(document.body);

            // Handles elements enhanced before HTMX became available.
            if (window.htmx) {
                window.htmx.process(document.body);
            }
        }

        this.refreshActiveLinks();
    }


    processExistingContainers() {
        document.querySelectorAll(
            "[data-spice-router-processed]"
        ).forEach(element => {
            delete element.dataset.spiceRouterProcessed;
        });

        this.processDocument();
    }


    /* ---------------------------------------------------------------------- */
    /* Active links                                                           */
    /* ---------------------------------------------------------------------- */

    refreshActiveLinks() {
        const currentURL = new URL(window.location.href);
        const currentPath = normalizePath(currentURL.pathname);

        document.querySelectorAll(
            "a[data-spice-link]"
        ).forEach(anchor => {
            let active = false;

            try {
                const linkURL = new URL(
                    anchor.href,
                    window.location.href
                );

                const linkPath = normalizePath(linkURL.pathname);

                const exact = anchor.dataset.spiceExact === "true";
                const matchQuery =
                    anchor.dataset.spiceMatchQuery === "true";

                if (exact) {
                    active = linkPath === currentPath;
                } else {
                    active =
                        linkPath === "/" ||
                        linkPath === currentPath ||
                        currentPath.startsWith(`${linkPath}/`);
                }

                if (
                    active &&
                    matchQuery &&
                    linkURL.search !== currentURL.search
                ) {
                    active = false;
                }
            } catch {
                active = false;
            }

            const activeClass =
                anchor.dataset.spiceActiveClass || "active";

            anchor.classList.toggle(activeClass, active);

            if (active) {
                anchor.setAttribute("aria-current", "page");
            } else {
                anchor.removeAttribute("aria-current");
            }
        });
    }


    /* ---------------------------------------------------------------------- */
    /* HTMX event listeners                                                   */
    /* ---------------------------------------------------------------------- */

    initListeners() {
        const events = {
            "htmx:beforeRequest": "beforeRequest",
            "htmx:beforeSwap": "beforeSwap",
            "htmx:afterSwap": "afterSwap",
            "htmx:afterRequest": "afterRequest",
            "htmx:pushedIntoHistory": "pushedIntoHistory",
            "htmx:responseError": "responseError",
            "htmx:sendError": "sendError",
            "htmx:timeout": "timeout",
            "htmx:sendAbort": "sendAbort",
        };

        for (const [event, handler] of Object.entries(events)) {
            document.addEventListener(
                event,
                this.boundHandlers[handler]
            );
        }

        window.addEventListener(
            "popstate",
            this.boundHandlers.popstate
        );
    }


    getTriggerElement(detail) {
        return (
            detail?.requestConfig?.elt ||
            detail?.elt ||
            null
        );
    }


    isRouterRequest(detail) {
        const element = this.getTriggerElement(detail);

        return Boolean(
            element?.matches?.("[data-spice-navigation]")
        );
    }


    handleBeforeRequest(event) {
        const detail = event.detail || {};

        if (!this.isRouterRequest(detail)) return;

        const element = this.getTriggerElement(detail);

        const beforeEvent = emit(
            element,
            ROUTER_EVENTS.BEFORE_NAVIGATE,
            {
                element,
                target: detail.target,
                xhr: detail.xhr,
                requestConfig: detail.requestConfig,
            },
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
            {
                element,
                target: detail.target,
                xhr: detail.xhr,
                requestConfig: detail.requestConfig,
            },
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

        emit(target, ROUTER_EVENTS.AFTER_SWAP, {
            element,
            target,
            xhr: detail.xhr,
        });

        emit(target, ROUTER_EVENTS.NAVIGATE, {
            element,
            target,
            url: window.location.href,
            xhr: detail.xhr,
        });

        this.refreshActiveLinks();
        this.initBoostContainers(target);
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


    /* ---------------------------------------------------------------------- */
    /* Dynamic DOM                                                            */
    /* ---------------------------------------------------------------------- */

    observeDOM() {
        if (this.observer || !document.body) return;

        this.observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType !== Node.ELEMENT_NODE) continue;

                    this.initBoostContainers(node);

                    // A newly added anchor may be inside an existing
                    // navigation container.
                    const parentContainer = node.closest?.(
                        CONTAINER_SELECTOR
                    );

                    if (parentContainer) {
                        this.processBoostContainer(parentContainer);
                    }
                }
            }

            this.refreshActiveLinks();
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }
}


/* -------------------------------------------------------------------------- */
/* Automatic initialization                                                  */
/* -------------------------------------------------------------------------- */

// Create one router instance for the entire application.
const spiceRouter = new SpiceRouter();

// Expose the singleton for diagnostics and optional configuration.
if (typeof window !== "undefined") {
    window.SpiceRouter = spiceRouter;

    // Register custom elements immediately, not after DOMContentLoaded.
    spiceRouter.registerElements();

    const start = () => {
        spiceRouter.start();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start, {
            once: true,
        });
    } else {
        start();
    }

    // If HTMX was loaded after the router module, process the page again
    // once all page resources have loaded.
    window.addEventListener("load", () => {
        spiceRouter.start();
        spiceRouter.processDocument();
    }, { once: true });
}
