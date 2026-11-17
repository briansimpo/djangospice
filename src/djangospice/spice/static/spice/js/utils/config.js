export const DEFAULTS = {
    target: "spice-app",
    select: "spice-app",
    swap: "innerHTML show:window:top",
    transition: false,
    preload: false,
    pushUrl: true,
};

export const HTTP_METHODS = new Set([
    "get", "post", "put", "patch", "delete",
]);

export const CONTAINER_SELECTOR = [
    "spice-app",
    "spice-nav",
    "spice-boost",
    "[spice-boost]",
].join(",");

export const ROUTER_EVENTS = {
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

export function emit(target, name, detail = {}, options = {}) {
    return (target || document).dispatchEvent(
        new CustomEvent(name, {
            bubbles: true,
            composed: true,
            cancelable: options.cancelable ?? false,
            detail,
        })
    );
}

export function parseBoolean(value, fallback = false) {
    if (value === null || value === undefined) return fallback;
    if (value === "") return true;
    return !["false", "0", "off", "no"].includes(String(value).toLowerCase());
}

export function normalizePath(path) {
    if (!path) return "/";
    let result = path.replace(/\/+/g, "/");
    if (result.length > 1) {
        result = result.replace(/\/$/, "");
    }
    return result || "/";
}

export function isInternalURL(value) {
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

export function shouldEnhanceAnchor(anchor) {
    if (!anchor?.hasAttribute("href")) return false;
    const href = anchor.getAttribute("href");
    if (!href || href.startsWith("#")) return false;

    try {
        const url = new URL(href, window.location.href);
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

export function resolveConfig(element) {
    const config = { ...DEFAULTS };
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

        const target = source.getAttribute(isRequestElement ? "hx-target" : "target");
        const select = source.getAttribute("select");
        const swap = source.getAttribute("swap");
        const transition = source.getAttribute("transition");
        const preload = source.getAttribute("preload");
        const pushUrl = source.getAttribute("push-url");

        if (target !== null) config.target = target;
        if (select !== null) config.select = select;
        if (swap !== null) config.swap = swap;
        if (transition !== null) {
            config.transition = parseBoolean(transition, config.transition);
        }
        if (preload !== null) {
            config.preload = parseBoolean(preload, config.preload);
        }
        if (pushUrl !== null) {
            config.pushUrl = parseBoolean(pushUrl, config.pushUrl);
        }
    };

    containers.forEach(container => apply(container));
    apply(element, true);

    config.target ||= "spice-app";
    config.select ||= config.target;
    config.swap ||= DEFAULTS.swap;

    return config;
}

export function copyAttributes(source, destination, excluded = new Set()) {
    for (const attribute of source.attributes) {
        const name = attribute.name;
        if (excluded.has(name) || name.startsWith("data-spice-internal-")) {
            continue;
        }
        destination.setAttribute(name, attribute.value);
    }
}