
/**
 * Djangospice - SpiceLookup
 *
 * Framework-agnostic searchable select controller.
 *
 * Features:
 * - Remote searching and pagination
 * - Single and multiple selection
 * - Cascading/dependent lookups
 * - HTMX compatibility
 * - Automatic initialization and cleanup
 *
 */

const SELECTOR = "select[data-spice-lookup]";
const EVENT_PREFIX = "spice:lookup";

const DEFAULTS = Object.freeze({
    delay: 250,
    pageSize: 20,
    minimumInputLength: 0,
    searchParam: "q",
    pageParam: "page",
    pageSizeParam: "page_size",
    placeholder: "Select...",
    searchPlaceholder: "Search...",
    allowClear: true,
    tokenHeader: "X-Lookup-Token",
});

const instances = new WeakMap();

/* ------------------------------------------------------------
 * Utilities
 * ------------------------------------------------------------ */

function parseBoolean(value, fallback) {
    if (value === undefined || value === null || value === "") {
        return fallback;
    }

    return String(value).toLowerCase() === "true";
}

function parseInteger(value, fallback) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function parseDependencies(value) {
    if (!value) return [];

    return String(value)
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
}

function debounce(callback, delay) {
    let timer = null;

    const debounced = function (...args) {
        window.clearTimeout(timer);
        timer = window.setTimeout(
            () => callback.apply(this, args),
            delay
        );
    };

    debounced.cancel = function () {
        window.clearTimeout(timer);
        timer = null;
    };

    return debounced;
}

function createElement(tag, className, attributes = {}) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    for (const [name, value] of Object.entries(attributes)) {
        if (value === null || value === undefined) continue;

        if (value === true) {
            element.setAttribute(name, "");
        } else if (value !== false) {
            element.setAttribute(name, String(value));
        }
    }

    return element;
}


export class SpiceLookup {
    constructor(select) {
        this.select = select;
        this.destroyed = false;
        this.loading = false;

        this.abortController = null;
        this.requestSequence = 0;

        this.page = 1;
        this.hasNext = false;
        this.highlightedIndex = -1;

        this.dependencies = [];
        this.dependencyListeners = [];

        this.config = this.readConfig();
        this.initialOptions = this.captureOptions();
        this.selectedValues = this.getSelectedValues();

        this.initialize();
    }

    readConfig() {
        const data = this.select.dataset;

        return {
            url: data.lookupUrl || "",
            name: data.lookupName || this.select.name || "",

            delay: parseInteger(data.lookupDelay, DEFAULTS.delay),

            pageSize: parseInteger(
                data.lookupPageSize,
                DEFAULTS.pageSize
            ),

            minimumInputLength: parseInteger(
                data.lookupMinSearchLength,
                DEFAULTS.minimumInputLength
            ),

            searchParam:
                data.lookupSearchParam || DEFAULTS.searchParam,

            pageParam:
                data.lookupPageParam || DEFAULTS.pageParam,

            pageSizeParam:
                data.lookupPageSizeParam || DEFAULTS.pageSizeParam,

            placeholder:
                data.lookupPlaceholder || DEFAULTS.placeholder,

            searchPlaceholder:
                data.lookupSearchPlaceholder ||
                DEFAULTS.searchPlaceholder,

            allowClear: parseBoolean(
                data.lookupAllowClear,
                DEFAULTS.allowClear
            ),

            token: data.lookupToken || null,

            tokenHeader:
                data.lookupTokenHeader || DEFAULTS.tokenHeader,
        };
    }

    initialize() {
        this.dependencies = this.readDependencies();

        this.createInterface();

        if (!this.wrapper) return;

        this.bindEvents();
        this.bindDependencies();

        this.syncDisabledState();
        this.syncFromSelect();
        this.renderInitialResults();
    }

    readDependencies() {
        return parseDependencies(
            this.select.dataset.lookupDependencies
        );
    }

    captureOptions() {
        return Array.from(this.select.options).map((option) => ({
            value: option.value,
            label: option.textContent,
            selected: option.selected,
            disabled: option.disabled,
        }));
    }

    hasDependencies() {
        return this.dependencies.length > 0;
    }

    /* --------------------------------------------------------
     * Interface
     * -------------------------------------------------------- */

    createInterface() {
        const parent = this.select.parentNode;

        if (!parent) return;

        this.wrapper = createElement("div", "spice-lookup");
        this.wrapper.dataset.djangospiceLookupWrapper = "";

        this.control = createElement(
            "div",
            "spice-lookup__control"
        );

        this.selection = this.select.multiple
            ? createElement("div", "spice-lookup__selection")
            : null;

        this.search = createElement(
            "input",
            "spice-lookup__input",
            {
                type: "search",
                autocomplete: "off",
                role: "combobox",
                "aria-autocomplete": "list",
                "aria-expanded": "false",
                "aria-haspopup": "listbox",
                placeholder: this.config.searchPlaceholder,
            }
        );

        this.clearButton = this.config.allowClear
            ? createElement("button", "spice-lookup__clear", {
                type: "button",
                "aria-label": "Clear selection",
            })
            : null;

        if (this.clearButton) {
            this.clearButton.textContent = "×";
        }

        this.listbox = createElement(
            "div",
            "spice-lookup__dropdown",
            {
                role: "listbox",
                tabindex: "-1",
            }
        );

        this.status = createElement(
            "div",
            "spice-lookup__status",
            {
                role: "status",
                "aria-live": "polite",
            }
        );

        this.status.hidden = true;

        if (this.selection) {
            this.control.appendChild(this.selection);
        }

        this.control.appendChild(this.search);

        if (this.clearButton) {
            this.control.appendChild(this.clearButton);
        }

        parent.insertBefore(this.wrapper, this.select);

        this.wrapper.appendChild(this.control);
        this.wrapper.appendChild(this.listbox);
        this.wrapper.appendChild(this.status);
        this.wrapper.appendChild(this.select);

        this.select.classList.add("spice-lookup__native");

        this.listbox.id = this.getListboxId();
        this.search.setAttribute("aria-controls", this.listbox.id);

        this.wrapper.classList.add("is-enhanced");
    }

    getListboxId() {
        if (this.select.id) {
            return `${this.select.id}-lookup-listbox`;
        }

        return `spice-lookup-${Math.random().toString(36).slice(2)}`;
    }

    syncDisabledState() {
        if (!this.wrapper) return;

        const disabled =
            this.select.disabled ||
            (this.hasDependencies() && !this.isDependencySatisfied());

        this.search.disabled = disabled;

        if (this.clearButton) {
            this.clearButton.disabled = disabled;
        }

        this.wrapper.classList.toggle("is-disabled", disabled);
        this.wrapper.setAttribute("aria-disabled", String(disabled));
    }

    renderInitialResults() {
        if (this.hasDependencies()) {
            const initialSelected = this.initialOptions.filter(
                (option) => option.selected && option.value !== ""
            );

            this.clearLookupResults();

            if (
                this.isDependencySatisfied() &&
                initialSelected.length
            ) {
                this.syncFromSelect();
            } else {
                this.clearDependentOptions();
            }

            this.syncDisabledState();
            this.close();
            return;
        }

        this.renderResults(
            this.initialOptions
                .filter((option) => option.value !== "")
                .map((option) => ({
                    value: option.value,
                    label: option.label,
                }))
        );

        this.syncFromSelect();
    }

    /* --------------------------------------------------------
     * Events
     * -------------------------------------------------------- */

    bindEvents() {
        this.handleSearch = debounce(
            () => this.searchLookup(),
            this.config.delay
        );

        this.search.addEventListener("input", this.handleSearch);

        this.search.addEventListener("click", () => {
            if (this.select.disabled) return;

            if (this.hasDependencies()) {
                if (!this.isDependencySatisfied()) {
                    this.clearLookupResults();
                    this.close();
                    this.syncDisabledState();
                    return;
                }

                this.page = 1;
                this.hasNext = false;

                this.clearLookupResults();

                this.load({
                    term: "",
                    page: 1,
                    replace: true,
                });
            }

            this.open();
        });

        this.search.addEventListener("keydown", (event) => {
            this.handleKeydown(event);
        });

        this.listbox.addEventListener("scroll", () => {
            this.checkLoadMore();
        });

        this.listbox.addEventListener("mousedown", (event) => {
            const option = event.target.closest("[data-lookup-option]");

            if (option) event.preventDefault();
        });

        this.listbox.addEventListener("click", (event) => {
            const option = event.target.closest("[data-lookup-option]");

            if (!option) return;

            this.selectResult(
                option.dataset.lookupValue,
                option.textContent
            );
        });

        if (this.selection) {
            this.selection.addEventListener("click", (event) => {
                const removeButton = event.target.closest(
                    "[data-lookup-remove]"
                );

                if (!removeButton) return;

                event.stopPropagation();

                this.toggleMultipleValue(
                    removeButton.dataset.lookupRemove
                );
            });
        }

        this.select.addEventListener("change", () => {
            this.syncFromSelect();
        });

        this.control.addEventListener("click", (event) => {
            if (event.target.closest("[data-lookup-remove]")) return;

            this.search.focus();
        });

        if (this.clearButton) {
            this.clearButton.addEventListener("click", () => {
                this.clearSelection();
            });
        }

        this.handleDocumentClick = (event) => {
            if (!this.wrapper.contains(event.target)) {
                this.close();
            }
        };

        document.addEventListener(
            "mousedown",
            this.handleDocumentClick
        );
    }

    /* --------------------------------------------------------
     * Dependencies
     * -------------------------------------------------------- */

    bindDependencies() {
        this.unbindDependencies();

        for (const dependency of this.dependencies) {
            const source = this.findDependency(dependency);

            if (!source) continue;

            const handler = () => this.handleDependencyChange();

            source.addEventListener("change", handler);

            this.dependencyListeners.push({
                element: source,
                handler,
            });
        }
    }

    unbindDependencies() {
        for (const { element, handler } of this.dependencyListeners) {
            element.removeEventListener("change", handler);
        }

        this.dependencyListeners = [];
    }

    findDependency(name) {
        if (!name) return null;

        // Avoid interpolating dependency names into CSS selectors.
        const candidates = document.querySelectorAll(
            "[data-lookup-name], [name]"
        );

        for (const element of candidates) {
            if (
                element.dataset.lookupName === name ||
                element.name === name
            ) {
                return element;
            }
        }

        return null;
    }

    isDependencySatisfied() {
        if (!this.hasDependencies()) return true;

        return this.dependencies.every((dependency) => {
            const value = this.getDependencyValue(dependency);

            if (Array.isArray(value)) {
                return value.length > 0;
            }

            return value !== null && value !== undefined && value !== "";
        });
    }

    handleDependencyChange() {
        if (!this.hasDependencies() || this.destroyed) return;

        this.requestSequence++;
        this.abortRequest();
        this.handleSearch.cancel();

        this.setLoading(false);
        this.close();

        this.clearSelection(false, {
            restoreInitial: false,
        });

        this.clearDependentOptions();
        this.clearLookupResults();

        this.page = 1;
        this.hasNext = false;

        this.syncDisabledState();
    }

    clearDependentOptions() {
        for (const option of Array.from(this.select.options)) {
            if (option.value !== "") {
                option.remove();
            } else {
                option.selected = true;
            }
        }

        if (
            !this.select.multiple &&
            !Array.from(this.select.options).some(
                (option) => option.value === ""
            )
        ) {
            this.select.add(new Option(this.config.placeholder, ""));
        }

        this.selectedValues = [];
        this.search.value = "";

        if (this.selection) {
            this.selection.innerHTML = "";
        }

        this.clearLookupResults();
    }

    getDependencyValue(name) {
        const element = this.findDependency(name);

        if (!element) return null;

        if (element.multiple) {
            return Array.from(element.selectedOptions)
                .map((option) => option.value)
                .filter(Boolean);
        }

        return element.value || null;
    }

    /* --------------------------------------------------------
     * Search and Loading
     * -------------------------------------------------------- */

    searchLookup() {
        if (this.destroyed) return;

        const term = this.search.value.trim();

        if (
            this.hasDependencies() &&
            !this.isDependencySatisfied()
        ) {
            this.clearLookupResults();
            this.close();
            return;
        }

        if (term.length < this.config.minimumInputLength) {
            if (this.hasDependencies()) return;

            this.clearRemoteResults({
                restoreInitial: true,
            });

            if (this.config.minimumInputLength) {
                const count = this.config.minimumInputLength;

                this.setStatus(
                    `Enter at least ${count} character${count === 1 ? "" : "s"}.`
                );
            }

            return;
        }

        this.page = 1;
        this.hasNext = false;

        this.load({
            term,
            page: 1,
            replace: true,
        });
    }

    async load({ term = "", page = 1, replace = true }) {
        if (
            this.destroyed ||
            !this.config.url ||
            !this.isDependencySatisfied()
        ) {
            return;
        }

        const requestId = ++this.requestSequence;

        this.abortRequest();

        const controller = new AbortController();
        this.abortController = controller;

        const url = new URL(
            this.config.url,
            window.location.origin
        );

        if (term) {
            url.searchParams.set(this.config.searchParam, term);
        }

        url.searchParams.set(this.config.pageParam, String(page));

        url.searchParams.set(
            this.config.pageSizeParam,
            String(this.config.pageSize)
        );

        this.appendDependencies(url);

        const headers = {
            Accept: "application/json",
        };

        if (this.config.token) {
            headers[this.config.tokenHeader] = this.config.token;
        }

        this.setLoading(true);

        try {
            const response = await fetch(url.toString(), {
                method: "GET",
                headers,
                credentials: "same-origin",
                signal: controller.signal,
            });

            if (
                this.destroyed ||
                requestId !== this.requestSequence
            ) {
                return;
            }

            if (!response.ok) {
                throw new Error(
                    `Lookup request failed: ${response.status}`
                );
            }

            const data = await response.json();

            if (
                this.destroyed ||
                requestId !== this.requestSequence
            ) {
                return;
            }

            this.handleResponse(data, {
                page,
                replace,
            });
        } catch (error) {
            if (error.name === "AbortError") return;

            if (
                this.destroyed ||
                requestId !== this.requestSequence
            ) {
                return;
            }

            this.setError("Unable to load results.");

            this.dispatch("error", {
                error,
            });
        } finally {
            if (requestId === this.requestSequence) {
                this.setLoading(false);
            }
        }
    }

    appendDependencies(url) {
        for (const dependency of this.dependencies) {
            const value = this.getDependencyValue(dependency);

            if (
                value === null ||
                value === undefined ||
                value === ""
            ) {
                continue;
            }

            if (Array.isArray(value)) {
                for (const item of value) {
                    url.searchParams.append(dependency, item);
                }
            } else {
                url.searchParams.set(dependency, value);
            }
        }
    }

    abortRequest() {
        if (!this.abortController) return;

        this.abortController.abort();
        this.abortController = null;
    }

    /* --------------------------------------------------------
     * Response and Rendering
     * -------------------------------------------------------- */

    handleResponse(data, { page, replace }) {
        const results = Array.isArray(data?.results)
            ? data.results
            : [];

        if (replace) {
            this.clearRemoteResults({
                restoreInitial: false,
            });
        }

        this.renderResults(results);

        const pagination = data?.pagination || {};

        this.hasNext = Boolean(
            pagination.has_next ?? pagination.more ?? false
        );

        this.page = page;

        if (!results.length && replace) {
            this.setEmpty();
        } else {
            this.clearStatus();
        }
    }

    renderResults(results) {
        const selected = new Set(this.getSelectedValues());

        const existing = new Set(
            Array.from(
                this.listbox.querySelectorAll("[data-lookup-option]")
            ).map((option) => option.dataset.lookupValue)
        );

        for (const result of results) {
            const value = result?.value ?? result?.id ?? "";
            const label = result?.label ?? result?.text ?? "";

            if (value === null || value === undefined || value === "") {
                continue;
            }

            const stringValue = String(value);

            if (existing.has(stringValue)) continue;

            const option = createElement(
                "div",
                "spice-lookup__option",
                {
                    role: "option",
                    "data-lookup-option": "",
                    "data-lookup-value": stringValue,
                }
            );

            option.textContent = String(label);

            const isSelected = selected.has(stringValue);

            option.classList.toggle("is-selected", isSelected);
            option.setAttribute("aria-selected", String(isSelected));

            this.listbox.appendChild(option);
            existing.add(stringValue);
        }

        this.updateHighlight();
    }

    checkLoadMore() {
        if (this.loading || !this.hasNext || this.destroyed) return;

        const threshold = 50;

        const position =
            this.listbox.scrollTop + this.listbox.clientHeight;

        const height = this.listbox.scrollHeight;

        if (height - position <= threshold) {
            this.load({
                term: this.search.value.trim(),
                page: this.page + 1,
                replace: false,
            });
        }
    }

    clearRemoteResults({ restoreInitial = true } = {}) {
        this.listbox.innerHTML = "";
        this.highlightedIndex = -1;

        if (restoreInitial && !this.hasDependencies()) {
            this.renderResults(
                this.initialOptions
                    .filter((option) => option.value !== "")
                    .map((option) => ({
                        value: option.value,
                        label: option.label,
                    }))
            );
        }

        this.hasNext = false;
        this.page = 1;

        this.clearStatus();
    }

    clearLookupResults() {
        this.listbox.innerHTML = "";
        this.highlightedIndex = -1;
        this.hasNext = false;
        this.page = 1;

        this.clearStatus();
    }

    setLoading(value) {
        if (this.destroyed) return;

        this.loading = value;

        this.wrapper.classList.toggle("is-loading", value);

        if (value) {
            this.setStatus("Loading...");
        } else if (this.status.textContent === "Loading...") {
            this.clearStatus();
        }
    }

    setEmpty() {
        this.setStatus("No results found.");
    }

    setError(message) {
        this.setStatus(message);
        this.wrapper.classList.add("has-error");
    }

    setStatus(message) {
        this.status.textContent = message;
        this.status.hidden = !message;
    }

    clearStatus() {
        this.status.textContent = "";
        this.status.hidden = true;

        this.wrapper.classList.remove("has-error");
    }

    /* --------------------------------------------------------
     * Selection
     * -------------------------------------------------------- */

    getSelectedValues() {
        return Array.from(this.select.selectedOptions)
            .map((option) => option.value);
    }

    selectResult(value, label = null) {
        if (value === null || value === undefined || value === "") {
            return;
        }

        if (this.select.multiple) {
            this.toggleMultipleValue(value, label);
        } else {
            this.setSingleValue(value, label);
        }
    }

    setSingleValue(value, label = null) {
        const stringValue = String(value);

        let option = Array.from(this.select.options).find(
            (existing) => existing.value === stringValue
        );

        if (!option) {
            option = new Option(
                label !== null ? String(label) : stringValue,
                stringValue,
                false,
                false
            );

            this.select.appendChild(option);
        } else if (label !== null) {
            option.textContent = String(label);
        }

        for (const existing of this.select.options) {
            existing.selected = existing === option;
        }

        this.selectedValues = this.getSelectedValues();

        this.syncFromSelect();
        this.dispatchChange();
        this.close();

        this.search.value = option.textContent;

        this.dispatch("select", {
            value: stringValue,
            label: option.textContent,
        });
    }

    toggleMultipleValue(value, label = null) {
        const stringValue = String(value);

        let found = false;

        for (const option of this.select.options) {
            if (option.value !== stringValue) continue;

            option.selected = !option.selected;
            found = true;
            break;
        }

        if (!found) {
            const option = new Option(
                label !== null ? String(label) : stringValue,
                stringValue,
                false,
                true
            );

            this.select.appendChild(option);
        }

        this.dispatchChange();
        this.syncFromSelect();

        this.search.value = "";
        this.search.focus();

        this.open();

        this.dispatch("select", {
            value: stringValue,
            label: this.getOptionLabel(stringValue),
        });
    }

    clearSelection(
        triggerChange = true,
        { restoreInitial = true } = {}
    ) {
        for (const option of this.select.options) {
            option.selected = false;
        }

        if (triggerChange) {
            this.dispatchChange();
        }

        this.syncFromSelect();

        this.clearRemoteResults({
            restoreInitial,
        });
    }

    syncFromSelect() {
        if (this.destroyed) return;

        const selectedValues = new Set(this.getSelectedValues());

        if (!this.select.multiple) {
            const selectedValue = this.getSelectedValues()[0];

            this.search.value = selectedValue
                ? this.getOptionLabel(selectedValue)
                : "";
        }

        const optionElements = this.listbox.querySelectorAll(
            "[data-lookup-option]"
        );

        optionElements.forEach((element) => {
            const isSelected = selectedValues.has(
                element.dataset.lookupValue
            );

            element.classList.toggle("is-selected", isSelected);

            element.setAttribute(
                "aria-selected",
                String(isSelected)
            );
        });

        if (this.selection) {
            this.selection.innerHTML = "";

            for (const value of selectedValues) {
                const label = this.getOptionLabel(value);

                const tag = createElement(
                    "span",
                    "spice-lookup__tag",
                    {
                        "data-lookup-tag": value,
                    }
                );

                tag.textContent = label;

                const removeButton = createElement(
                    "button",
                    "spice-lookup__tag-remove",
                    {
                        type: "button",
                        "aria-label": `Remove ${label}`,
                        "data-lookup-remove": value,
                    }
                );

                removeButton.textContent = "×";

                tag.appendChild(removeButton);
                this.selection.appendChild(tag);
            }
        }
    }

    getOptionLabel(value) {
        const option = Array.from(this.select.options).find(
            (item) => item.value === String(value)
        );

        if (option) return option.textContent;

        const optionElement = Array.from(
            this.listbox.querySelectorAll("[data-lookup-option]")
        ).find(
            (item) => item.dataset.lookupValue === String(value)
        );

        return optionElement
            ? optionElement.textContent
            : String(value);
    }

    dispatchChange() {
        this.select.dispatchEvent(
            new Event("change", {
                bubbles: true,
            })
        );
    }

    dispatch(eventName, detail = {}) {
        if (!this.wrapper) return;

        this.wrapper.dispatchEvent(
            new CustomEvent(`${EVENT_PREFIX}:${eventName}`, {
                detail,
                bubbles: true,
                cancelable: true,
            })
        );
    }

    /* --------------------------------------------------------
     * Dropdown
     * -------------------------------------------------------- */

    open() {
        if (
            this.destroyed ||
            this.select.disabled ||
            (
                this.hasDependencies() &&
                !this.isDependencySatisfied()
            )
        ) {
            return;
        }

        this.wrapper.classList.add("is-open");

        this.search.setAttribute("aria-expanded", "true");
    }

    close() {
        if (!this.wrapper) return;

        this.wrapper.classList.remove("is-open");

        this.search.setAttribute("aria-expanded", "false");

        this.highlightedIndex = -1;

        this.updateHighlight();
    }

    handleKeydown(event) {
        const options = Array.from(
            this.listbox.querySelectorAll("[data-lookup-option]")
        );

        switch (event.key) {
            case "ArrowDown":
                event.preventDefault();

                if (!this.wrapper.classList.contains("is-open")) {
                    this.open();
                } else if (options.length) {
                    this.highlightedIndex =
                        (this.highlightedIndex + 1) % options.length;

                    this.updateHighlight();

                    this.scrollHighlightedIntoView(
                        options[this.highlightedIndex]
                    );
                }

                break;

            case "ArrowUp":
                event.preventDefault();

                if (options.length) {
                    this.highlightedIndex =
                        (
                            this.highlightedIndex -
                            1 +
                            options.length
                        ) % options.length;

                    this.updateHighlight();

                    this.scrollHighlightedIntoView(
                        options[this.highlightedIndex]
                    );
                }

                break;

            case "Enter":
                if (
                    this.wrapper.classList.contains("is-open") &&
                    this.highlightedIndex >= 0 &&
                    options[this.highlightedIndex]
                ) {
                    event.preventDefault();

                    const option = options[this.highlightedIndex];

                    this.selectResult(
                        option.dataset.lookupValue,
                        option.textContent
                    );
                }

                break;

            case "Escape":
                if (this.wrapper.classList.contains("is-open")) {
                    event.preventDefault();
                    this.close();
                }

                break;
        }
    }

    updateHighlight() {
        if (!this.listbox) return;

        const options = Array.from(
            this.listbox.querySelectorAll("[data-lookup-option]")
        );

        options.forEach((element, index) => {
            element.classList.toggle(
                "is-highlighted",
                index === this.highlightedIndex
            );
        });
    }

    scrollHighlightedIntoView(optionElement) {
        if (!optionElement) return;

        const parentRect = this.listbox.getBoundingClientRect();
        const optionRect = optionElement.getBoundingClientRect();

        if (optionRect.bottom > parentRect.bottom) {
            this.listbox.scrollTop +=
                optionRect.bottom - parentRect.bottom;
        } else if (optionRect.top < parentRect.top) {
            this.listbox.scrollTop -=
                parentRect.top - optionRect.top;
        }
    }

    /* --------------------------------------------------------
     * Cleanup
     * -------------------------------------------------------- */

    destroy() {
        if (this.destroyed) return;

        this.destroyed = true;

        // Invalidate any request that may still be resolving.
        this.requestSequence++;

        this.abortRequest();

        if (this.handleSearch) {
            this.handleSearch.cancel();
        }

        document.removeEventListener(
            "mousedown",
            this.handleDocumentClick
        );

        this.unbindDependencies();

        if (this.wrapper?.parentNode) {
            this.wrapper.parentNode.insertBefore(
                this.select,
                this.wrapper
            );

            this.wrapper.remove();
        }

        this.select.classList.remove("spice-lookup__native");
    }
}


export function initializeLookup(root = document) {
    if (!root) return;

    const selects = [];

    if (
        root.nodeType === Node.ELEMENT_NODE &&
        root.matches(SELECTOR)
    ) {
        selects.push(root);
    }

    if (typeof root.querySelectorAll === "function") {
        selects.push(...root.querySelectorAll(SELECTOR));
    }

    for (const select of selects) {
        if (instances.has(select)) continue;

        const instance = new SpiceLookup(select);
        instances.set(select, instance);
    }
}

export function destroyLookup(root) {
    if (!root) return;

    const selects = [];

    if (
        root.nodeType === Node.ELEMENT_NODE &&
        root.matches(SELECTOR)
    ) {
        selects.push(root);
    }

    if (typeof root.querySelectorAll === "function") {
        selects.push(...root.querySelectorAll(SELECTOR));
    }

    for (const select of selects) {
        const instance = instances.get(select);

        if (!instance) continue;

        instance.destroy();
        instances.delete(select);
    }
}

