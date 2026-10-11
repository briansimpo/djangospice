(function (window, document) {
    "use strict";

    const SELECTOR = "select[data-djangospice-lookup]";
    const EVENT_PREFIX = "djangospice:lookup";

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
        if (!value) {
            return [];
        }
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
                delay,
            );
        };

        debounced.cancel = function () {
            window.clearTimeout(timer);
            timer = null;
        };

        return debounced;
    }

    function escapeSelector(value) {
        if (window.CSS && typeof window.CSS.escape === "function") {
            return window.CSS.escape(value);
        }
        return String(value).replace(/[\^$.*+?()[\]{}|]/g, "\\$&");
    }

    function createElement(tag, className, attributes = {}) {
        const element = document.createElement(tag);
        if (className) {
            element.className = className;
        }
        for (const [name, value] of Object.entries(attributes)) {
            if (value === null || value === undefined) {
                continue;
            }
            if (value === true) {
                element.setAttribute(name, "");
            } else if (value !== false) {
                element.setAttribute(name, String(value));
            }
        }
        return element;
    }

    class LookupController {

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
                delay: DEFAULTS.delay,
                pageSize: parseInteger(data.lookupPageSize, DEFAULTS.pageSize),
                minimumInputLength: parseInteger(data.lookupMinSearchLength, DEFAULTS.minimumInputLength),
                searchParam: data.lookupSearchParam || DEFAULTS.searchParam,
                pageParam: data.lookupPageParam || DEFAULTS.pageParam,
                pageSizeParam: data.lookupPageSizeParam || DEFAULTS.pageSizeParam,
                placeholder: data.lookupPlaceholder || DEFAULTS.placeholder,
                searchPlaceholder: data.lookupSearchPlaceholder || DEFAULTS.searchPlaceholder,
                allowClear: parseBoolean(data.lookupAllowClear, DEFAULTS.allowClear),
                token: data.lookupToken || null,
                tokenHeader: data.lookupTokenHeader || DEFAULTS.tokenHeader,
            };
        }

        initialize() {
            this.dependencies = this.readDependencies();
            this.createInterface();
            this.bindEvents();
            this.bindDependencies();
            this.syncDisabledState();
            this.syncFromSelect();
            this.renderInitialResults();
        }

        readDependencies() {
            return parseDependencies(this.select.dataset.lookupDependencies);
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
       
        renderInitialResults() {
            // Dependent lookups must NEVER display backend-rendered defaults.
            if (this.hasDependencies()) {
                this.clearLookupResults();
                this.clearDependentOptions();
                this.syncDisabledState();

                // If the parent is already selected, fetch dependent options.
                if (this.isDependencySatisfied()) {
                    this.load({
                        term: "",
                        page: 1,
                        replace: true,
                    });
                }

                return;
            }

            // Independent lookups retain their normal initial options.
            this.renderResults(
                this.initialOptions
                    .filter((option) => option.value !== "")
                    .map((option) => ({
                        value: option.value,
                        label: option.label,
                    }))
            );
        }

        createInterface() {
            const parent = this.select.parentNode;
            if (!parent) return;

            this.wrapper = createElement("div", "djangospice-lookup");
            this.wrapper.dataset.djangospiceLookupWrapper = "";

            if (this.select.multiple) {
                this.selection = createElement("div", "djangospice-lookup__selection");
            } else {
                this.selection = null;
            }

            this.search = createElement("input", "djangospice-lookup__input", {
                type: "search",
                autocomplete: "off",
                role: "combobox",
                "aria-autocomplete": "list",
                "aria-expanded": "false",
                "aria-haspopup": "listbox",
                placeholder: this.config.searchPlaceholder,
            });

            if (this.config.allowClear) {
                this.clearButton = createElement("button", "djangospice-lookup__clear", {
                    type: "button",
                    "aria-label": "Clear selection",
                });
                this.clearButton.textContent = "×";
            } else {
                this.clearButton = null;
            }

            this.listbox = createElement("div", "djangospice-lookup__dropdown", {
                role: "listbox",
                tabindex: "-1",
            });

            this.status = createElement("div", "djangospice-lookup__status", {
                role: "status",
                "aria-live": "polite",
            });
            this.status.hidden = true;

            parent.insertBefore(this.wrapper, this.select);

            if (this.selection) {
                this.wrapper.appendChild(this.selection);
            }
            this.wrapper.appendChild(this.search);
            if (this.clearButton) {
                this.wrapper.appendChild(this.clearButton);
            }
            this.wrapper.appendChild(this.listbox);
            this.wrapper.appendChild(this.status);
            this.wrapper.appendChild(this.select);

            this.select.classList.add("djangospice-lookup__native");
            this.listbox.id = this.getListboxId();
            this.search.setAttribute("aria-controls", this.listbox.id);
            this.wrapper.classList.add("is-enhanced");
        }

        syncDisabledState() {
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

        getListboxId() {
            if (this.select.id) {
                return `${this.select.id}-lookup-listbox`;
            }
            return `djangospice-lookup-${Math.random().toString(36).slice(2)}`;
        }

        // ============================================================
        // Events
        // ============================================================

        bindEvents() {
            this.handleSearch = debounce(() => {
                this.searchLookup();
            }, this.config.delay);

            this.search.addEventListener("input", this.handleSearch);

            this.search.addEventListener("focus", () => {
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
                if (option) {
                    event.preventDefault();
                }
            });

            this.listbox.addEventListener("click", (event) => {
                const option = event.target.closest("[data-lookup-option]");
                if (!option) return;
                this.selectResult(
                    option.dataset.lookupValue,
                    option.textContent,
                );
            });

            if (this.selection) {
                this.selection.addEventListener("click", (event) => {
                    const removeBtn = event.target.closest("[data-lookup-remove]");
                    if (!removeBtn) return;
                    event.stopPropagation();
                    this.toggleMultipleValue(removeBtn.dataset.lookupRemove);
                });
            }

            this.select.addEventListener("change", () => {
                this.syncFromSelect();
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

            document.addEventListener("mousedown", this.handleDocumentClick);
        }

        // ============================================================
        // Dependencies
        // ============================================================

        bindDependencies() {
            for (const dependency of this.dependencies) {
                const source = this.findDependency(dependency);
                if (!source) continue;

                const handler = () => {
                    this.handleDependencyChange();
                };

                source.addEventListener("change", handler);
                this.dependencyListeners.push({ element: source, handler });
            }
        }

        findDependency(name) {
            if (!name) return null;
            const lookup = document.querySelector(`[data-lookup-name="${escapeSelector(name)}"]`);
            if (lookup) return lookup;
            return document.querySelector(`[name="${escapeSelector(name)}"]`);
        }

        isDependencySatisfied() {
            if (!this.hasDependencies()) {
                return true;
            }

            return this.dependencies.every((dependency) => {
                const value = this.getDependencyValue(dependency);
                if (Array.isArray(value)) {
                    return value.length > 0;
                }
                return value !== null && value !== undefined && value !== "";
            });
        }

            
        handleDependencyChange() {
            if (!this.hasDependencies()) {
                return;
            }

            // Invalidate pending requests and debounced searches.
            this.requestSequence++;
            this.abortRequest();
            this.handleSearch.cancel();

            this.close();

            // Never retain child selections or backend defaults.
            this.clearSelection(false, { restoreInitial: false });
            this.clearDependentOptions();

            this.page = 1;
            this.hasNext = false;

            const satisfied = this.isDependencySatisfied();
            this.syncDisabledState();

            if (!satisfied) {
                // Parent was cleared: keep the child empty and disabled.
                return;
            }

            // Parent has a value: fetch options from the backend.
            this.load({
                term: "",
                page: 1,
                replace: true,
            });
        }


        clearDependentOptions() {
            // Remove every non-placeholder option.
            for (const option of Array.from(this.select.options)) {
                if (option.value !== "") {
                    option.remove();
                } else {
                    option.selected = true;
                }
            }

            // Ensure a single-select always has a valid empty choice.
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
                return Array.from(element.selectedOptions).map((option) => option.value).filter(Boolean);
            }
            return element.value || null;
        }

        // ============================================================
        // Search & Loading
        // ============================================================

        searchLookup() {
            const term = this.search.value.trim();

            if (this.hasDependencies() && !this.isDependencySatisfied()) {
                this.clearLookupResults();
                return;
            }

            if (term.length < this.config.minimumInputLength) {
                if (this.hasDependencies()) {
                    this.clearRemoteResults({ restoreInitial: false });
                    if (this.isDependencySatisfied()) {
                        this.load({ term: "", page: 1, replace: true });
                    }
                } else {
                    this.clearRemoteResults({ restoreInitial: true });
                }

                if (this.config.minimumInputLength) {
                    this.setStatus(
                        `Enter at least ${this.config.minimumInputLength} character${
                            this.config.minimumInputLength === 1 ? "" : "s"
                        }.`
                    );
                }
                return;
            }

            this.page = 1;
            this.hasNext = false;
            this.load({ term, page: 1, replace: true });
        }

        async load({ term = "", page = 1, replace = true }) {
            if (this.destroyed || !this.config.url || !this.isDependencySatisfied()) {
                return;
            }

            const requestId = ++this.requestSequence;
            this.abortRequest();
            this.abortController = new AbortController();

            const url = new URL(this.config.url, window.location.origin);
            if (term) {
                url.searchParams.set(this.config.searchParam, term);
            }
            url.searchParams.set(this.config.pageParam, String(page));
            url.searchParams.set(this.config.pageSizeParam, String(this.config.pageSize));
            this.appendDependencies(url);

            const headers = { Accept: "application/json" };
            if (this.config.token) {
                headers[this.config.tokenHeader] = this.config.token;
            }

            this.setLoading(true);

            try {
                const response = await fetch(url.toString(), {
                    method: "GET",
                    headers,
                    credentials: "same-origin",
                    signal: this.abortController.signal,
                });

                if (this.destroyed || requestId !== this.requestSequence) return;

                if (!response.ok) {
                    throw new Error(`Lookup request failed: ${response.status}`);
                }

                const data = await response.json();
                this.handleResponse(data, { page, replace });
            } catch (error) {
                if (error.name === "AbortError") return;
                this.setError("Unable to load results.");
                this.dispatch("error", { error });
            } finally {
                if (requestId === this.requestSequence) {
                    this.setLoading(false);
                }
            }
        }

        appendDependencies(url) {
            for (const dependency of this.dependencies) {
                const value = this.getDependencyValue(dependency);
                if (value === null || value === undefined || value === "") continue;
                if (Array.isArray(value)) {
                    for (const item of value) {
                        url.searchParams.append(dependency, item);
                    }
                    continue;
                }
                url.searchParams.set(dependency, value);
            }
        }

        abortRequest() {
            if (this.abortController) {
                this.abortController.abort();
                this.abortController = null;
            }
        }

        // ============================================================
        // Response & Rendering
        // ============================================================

        handleResponse(data, { page, replace }) {
            const results = Array.isArray(data?.results) ? data.results : [];
            if (replace) {
                this.clearRemoteResults({ restoreInitial: false });
            }
            this.renderResults(results);

            const pagination = data?.pagination || {};
            this.hasNext = Boolean(pagination.has_next ?? pagination.more ?? false);
            this.page = page;

            if (!results.length && replace) {
                this.setEmpty();
            } else {
                this.clearStatus();
            }
            this.open();
        }

        renderResults(results) {
            const selected = new Set(this.getSelectedValues());
            const existing = new Set(
                Array.from(this.listbox.querySelectorAll("[data-lookup-option]")).map(
                    (option) => option.dataset.lookupValue
                )
            );

            for (const result of results) {
                const value = result?.value ?? result?.id ?? "";
                const label = result?.label ?? result?.text ?? "";
                if (!value) continue;

                const stringValue = String(value);
                if (existing.has(stringValue)) continue;

                const option = createElement("div", "djangospice-lookup__option", {
                    role: "option",
                    "data-lookup-option": "",
                    "data-lookup-value": stringValue,
                });
                option.textContent = label;
                if (selected.has(stringValue)) {
                    option.classList.add("is-selected");
                    option.setAttribute("aria-selected", "true");
                } else {
                    option.setAttribute("aria-selected", "false");
                }

                this.listbox.appendChild(option);
                existing.add(stringValue);
            }
            this.updateHighlight();
        }

        checkLoadMore() {
            if (this.loading || !this.hasNext) return;
            const threshold = 50;
            const position = this.listbox.scrollTop + this.listbox.clientHeight;
            const height = this.listbox.scrollHeight;

            if (height - position <= threshold) {
                const term = this.search.value.trim();
                this.load({ term, page: this.page + 1, replace: false });
            }
        }

                
        clearRemoteResults({ restoreInitial = true } = {}) {
            this.listbox.innerHTML = "";
            this.highlightedIndex = -1;

            // Only independent lookups may restore backend defaults.
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

        getSelectedValues() {
            return Array.from(this.select.selectedOptions).map((option) => option.value);
        }

        selectResult(value, label = null) {
            if (!value) return;
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
                if (option.value === stringValue) {
                    option.selected = !option.selected;
                    found = true;
                    break;
                }
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

        clearSelection(triggerChange = true, { restoreInitial = true } = {}) {
            for (const option of this.select.options) {
                option.selected = false;
            }

            if (triggerChange) {
                this.dispatchChange();
            }

            this.syncFromSelect();

            this.clearRemoteResults({ restoreInitial });

            // Dependent lookups must fetch fresh options after being cleared.
            // Keep the current parent selection and use it in the request.
            if (triggerChange && this.hasDependencies()) {
                if (this.isDependencySatisfied()) {
                    this.load({
                        term: "",
                        page: 1,
                        replace: true,
                    });
                } else {
                    this.clearDependentOptions();
                    this.syncDisabledState();
                }
            }
        }

        syncFromSelect() {
            const selectedValues = new Set(this.getSelectedValues());

            if (!this.select.multiple) {
                const selectedValue = this.getSelectedValues()[0];
                this.search.value = selectedValue
                    ? this.getOptionLabel(selectedValue)
                    : "";
            }

            const optionEls = this.listbox.querySelectorAll("[data-lookup-option]");
            optionEls.forEach((el) => {
                const isSelected = selectedValues.has(el.dataset.lookupValue);
                el.classList.toggle("is-selected", isSelected);
                el.setAttribute("aria-selected", String(isSelected));
            });

            if (this.selection) {
                this.selection.innerHTML = "";
                for (const value of selectedValues) {
                    const label = this.getOptionLabel(value);
                    const tag = createElement("span", "djangospice-lookup__tag", {
                        "data-lookup-tag": value,
                    });
                    tag.textContent = label;

                    const removeBtn = createElement("button", "djangospice-lookup__tag-remove", {
                        type: "button",
                        "aria-label": `Remove ${label}`,
                        "data-lookup-remove": value,
                    });
                    removeBtn.textContent = "×";
                    tag.appendChild(removeBtn);
                    this.selection.appendChild(tag);
                }
            }
        }

        getOptionLabel(value) {
            const option = Array.from(this.select.options).find((opt) => opt.value === String(value));
            if (option) return option.textContent;
            const optionEl = this.listbox.querySelector(`[data-lookup-value="${escapeSelector(value)}"]`);
            if (optionEl) return optionEl.textContent;
            return value;
        }

        dispatchChange() {
            this.select.dispatchEvent(new Event("change", { bubbles: true }));
        }

        dispatch(eventName, detail = {}) {
            const event = new CustomEvent(`${EVENT_PREFIX}:${eventName}`, {
                detail,
                bubbles: true,
                cancelable: true,
            });
            this.wrapper.dispatchEvent(event);
        }

        open() {
            if (
                this.select.disabled ||
                (this.hasDependencies() && !this.isDependencySatisfied())
            ) {
                return;
            }
            this.wrapper.classList.add("is-open");
            this.search.setAttribute("aria-expanded", "true");
        }

        close() {
            this.wrapper.classList.remove("is-open");
            this.search.setAttribute("aria-expanded", "false");
            this.highlightedIndex = -1;
            this.updateHighlight();
        }

        handleKeydown(event) {
            const options = Array.from(this.listbox.querySelectorAll("[data-lookup-option]"));

            switch (event.key) {
                case "ArrowDown":
                    event.preventDefault();
                    if (!this.wrapper.classList.contains("is-open")) {
                        this.open();
                    } else if (options.length) {
                        this.highlightedIndex = (this.highlightedIndex + 1) % options.length;
                        this.updateHighlight();
                        this.scrollHighlightedIntoView(options[this.highlightedIndex]);
                    }
                    break;

                case "ArrowUp":
                    event.preventDefault();
                    if (options.length) {
                        this.highlightedIndex = (this.highlightedIndex - 1 + options.length) % options.length;
                        this.updateHighlight();
                        this.scrollHighlightedIntoView(options[this.highlightedIndex]);
                    }
                    break;

                case "Enter":
                    if (this.wrapper.classList.contains("is-open") && this.highlightedIndex >= 0 && options[this.highlightedIndex]) {
                        event.preventDefault();
                        const option = options[this.highlightedIndex];
                        this.selectResult(
                            option.dataset.lookupValue,
                            option.textContent,
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
            const options = Array.from(this.listbox.querySelectorAll("[data-lookup-option]"));
            options.forEach((el, index) => {
                const isHighlighted = index === this.highlightedIndex;
                el.classList.toggle("is-highlighted", isHighlighted);
            });
        }

        scrollHighlightedIntoView(optionEl) {
            if (!optionEl) return;
            const parent = this.listbox;
            const parentRect = parent.getBoundingClientRect();
            const optionRect = optionEl.getBoundingClientRect();

            if (optionRect.bottom > parentRect.bottom) {
                parent.scrollTop += optionRect.bottom - parentRect.bottom;
            } else if (optionRect.top < parentRect.top) {
                parent.scrollTop -= parentRect.top - optionRect.top;
            }
        }

        destroy() {
            this.destroyed = true;
            this.abortRequest();
            this.handleSearch.cancel();
            document.removeEventListener("mousedown", this.handleDocumentClick);

            for (const { element, handler } of this.dependencyListeners) {
                element.removeEventListener("change", handler);
            }

            if (this.wrapper && this.wrapper.parentNode) {
                this.wrapper.parentNode.insertBefore(this.select, this.wrapper);
                this.wrapper.remove();
            }
            this.select.classList.remove("djangospice-lookup__native");
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(SELECTOR).forEach((select) => {
            if (!instances.has(select)) {
                instances.set(select, new LookupController(select));
            }
        });
    });

})(window, document);