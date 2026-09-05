(() => {
    "use strict";


    // ------------------------------------------------------------------
    // Constants
    // ------------------------------------------------------------------

    const SELECTOR = "select[data-djangospice-lookup]";

    const NAMESPACE = ".djangospiceLookup";

    const DEFAULTS = Object.freeze({
        delay: 250,
        pageSize: 20,
        minimumInputLength: 0,
    });


    // ------------------------------------------------------------------
    // Utilities
    // ------------------------------------------------------------------

    function parseInteger(value, fallback) {
        const parsed = Number.parseInt(value, 10);

        return Number.isFinite(parsed)
            ? parsed
            : fallback;
    }


    function parseBoolean(value, fallback = false) {
        if (value === undefined || value === null) {
            return fallback;
        }

        return value === "true"
            || value === ""
            || value === true;
    }


    function escapeSelector(value) {
        return CSS.escape(String(value));
    }


    // ------------------------------------------------------------------
    // LookupController
    // ------------------------------------------------------------------

    class LookupController {

        constructor(element) {
            this.element = element;

            this.url =
                element.dataset.lookupUrl;

            this.pageSize =
                parseInteger(
                    element.dataset.lookupPageSize,
                    DEFAULTS.pageSize,
                );

            this.minimumInputLength =
                parseInteger(
                    element.dataset.lookupMinSearchLength,
                    DEFAULTS.minimumInputLength,
                );

            this.placeholder =
                element.dataset.lookupPlaceholder
                || "Select...";

            this.searchPlaceholder =
                element.dataset.lookupSearchPlaceholder
                || "Search...";

            this.allowClear =
                parseBoolean(
                    element.dataset.lookupAllowClear,
                    true,
                );

            this.dependencies =
                this.parseDependencies();

            /*
             * Native event listeners attached to dependency controls
             * must retain their exact callback references so they can
             * be removed during destroy().
             */
            this.dependencyListeners = [];

            this.initialized = false;

            this.initialize();
        }


        // --------------------------------------------------------------
        // Initialization
        // --------------------------------------------------------------

        initialize() {
            if (this.initialized) {
                return;
            }

            if (!this.url) {
                console.warn(
                    "DjangoSpice LookupWidget: "
                    + "missing lookup URL.",
                    this.element,
                );

                return;
            }

            if (
                typeof window.jQuery === "undefined"
                || typeof window.jQuery.fn.select2 !== "function"
            ) {
                console.warn(
                    "DjangoSpice LookupWidget: "
                    + "Select2 is required.",
                    this.element,
                );

                return;
            }

            this.$element =
                window.jQuery(this.element);

            this.initializeSelect2();

            this.bindDependencies();

            this.initialized = true;
        }


        initializeSelect2() {
            const controller = this;

            this.$element.select2({
                width: "100%",

                placeholder: this.placeholder,

                allowClear: this.allowClear,

                minimumInputLength:
                    this.minimumInputLength,

                ajax: {
                    url: this.url,

                    dataType: "json",

                    delay: DEFAULTS.delay,

                    cache: true,

                    data(params) {
                        return controller.buildRequestData(
                            params,
                        );
                    },

                    processResults(data, params) {
                        return controller.processResults(
                            data,
                            params,
                        );
                    },
                },
            });
        }


        // --------------------------------------------------------------
        // Dependencies
        // --------------------------------------------------------------

        parseDependencies() {
            const value =
                this.element.dataset.lookupDependencies
                || "";

            if (!value.trim()) {
                return [];
            }

            return value
                .split(",")
                .map(path => path.trim())
                .filter(Boolean);
        }


        bindDependencies() {
            for (const dependency of this.dependencies) {
                const controls =
                    this.findDependencyControls(
                        dependency,
                    );

                for (const control of controls) {
                    this.bindDependency(control);
                }
            }
        }


        bindDependency(control) {
            const $control =
                window.jQuery(control);

            /*
             * Remove any stale DjangoSpice handler that may already
             * exist on this control.
             */
            $control.off(
                `change${NAMESPACE}`,
            );

            const changeHandler = () => {
                this.handleDependencyChange();
            };

            const lookupChangeHandler = () => {
                this.handleDependencyChange();
            };

            /*
             * jQuery event.
             */
            $control.on(
                `change${NAMESPACE}`,
                changeHandler,
            );

            /*
             * DjangoSpice-specific lookup event.
             */
            control.addEventListener(
                "djangospice:lookup:change",
                lookupChangeHandler,
            );

            this.dependencyListeners.push({
                control,
                lookupChangeHandler,
            });
        }


        findDependencyControls(path) {
            const controls = [];

            /*
             * Prefer a DjangoSpice lookup widget whose
             * name matches the dependency path.
             */
            const lookupSelector =
                `[data-lookup-name="${escapeSelector(path)}"]`;

            document
                .querySelectorAll(lookupSelector)
                .forEach(control => {
                    controls.push(control);
                });


            /*
             * Normal Django form/filter controls.
             */
            const nameSelector =
                `[name="${escapeSelector(path)}"]`;

            document
                .querySelectorAll(nameSelector)
                .forEach(control => {
                    if (!controls.includes(control)) {
                        controls.push(control);
                    }
                });

            return controls;
        }


        getDependencyValue(path) {
            const controls =
                this.findDependencyControls(path);

            if (!controls.length) {
                return null;
            }

            /*
             * Prefer the first control because a named
             * Django form field normally has one widget.
             */
            const control = controls[0];


            /*
             * DjangoSpice LookupWidget.
             */
            if (
                control.matches(
                    "select[data-djangospice-lookup]",
                )
            ) {
                return this.getSelectValue(control);
            }


            /*
             * Native <select multiple>.
             */
            if (
                control instanceof HTMLSelectElement
                && control.multiple
            ) {
                const values =
                    Array.from(
                        control.selectedOptions,
                    )
                        .map(option => option.value)
                        .filter(Boolean);

                return values.length
                    ? values
                    : null;
            }


            /*
             * Checkbox groups.
             */
            if (
                controls.length > 1
                && controls.every(
                    item =>
                        item instanceof HTMLInputElement
                        && item.type === "checkbox",
                )
            ) {
                const values =
                    controls
                        .filter(control => control.checked)
                        .map(control => control.value)
                        .filter(Boolean);

                return values.length
                    ? values
                    : null;
            }

            return control.value || null;
        }


        getSelectValue(select) {
            const $select =
                window.jQuery(select);

            const value =
                $select.val();

            if (
                value === null
                || value === undefined
                || value === ""
            ) {
                return null;
            }

            if (Array.isArray(value)) {
                return value.filter(Boolean);
            }

            return value;
        }


        getDependencies() {
            const dependencies = {};

            for (const path of this.dependencies) {
                dependencies[path] =
                    this.getDependencyValue(path);
            }

            return dependencies;
        }


        handleDependencyChange() {
            /*
             * A child selection may no longer be valid
             * after one of its dependencies changes.
             */
            this.clear();

            /*
             * Select2's AJAX transport reads dependency
             * values dynamically on every request, so
             * no URL reconstruction is necessary here.
             */
        }


        clear() {
            if (!this.$element) {
                return;
            }

            this.$element
                .val(null)
                .trigger("change");
        }


        // --------------------------------------------------------------
        // AJAX
        // --------------------------------------------------------------

        buildRequestData(params) {
            const data = {
                q: params.term || "",

                page:
                    params.page || 1,

                page_size:
                    this.pageSize,
            };

            const dependencies =
                this.getDependencies();

            for (
                const [path, value]
                of Object.entries(dependencies)
            ) {
                if (
                    value === null
                    || value === undefined
                    || value === ""
                ) {
                    continue;
                }

                data[path] = value;
            }

            return data;
        }


        processResults(data, params) {
            params.page =
                params.page || 1;

            const results =
                Array.isArray(data.results)
                    ? data.results
                    : [];

            return {
                results:
                    results.map(
                        result =>
                            this.serializeResult(result),
                    ),

                pagination: {
                    more:
                        Boolean(
                            data.pagination?.has_next,
                        ),
                },
            };
        }


        serializeResult(result) {
            return {
                id: String(result.value),

                text: result.label,

                description:
                    result.description ?? null,
            };
        }


        // --------------------------------------------------------------
        // Destruction
        // --------------------------------------------------------------

        destroy() {
            if (!this.initialized) {
                return;
            }

            this.initialized = false;


            /*
             * Remove native DjangoSpice lookup event listeners.
             */
            for (
                const listener
                of this.dependencyListeners
            ) {
                listener.control.removeEventListener(
                    "djangospice:lookup:change",
                    listener.lookupChangeHandler,
                );
            }

            this.dependencyListeners = [];


            /*
             * Remove jQuery dependency listeners.
             *
             * The namespace ensures that only DjangoSpice's
             * handlers are removed.
             */
            for (const dependency of this.dependencies) {
                const controls =
                    this.findDependencyControls(
                        dependency,
                    );

                for (const control of controls) {
                    window.jQuery(control).off(
                        `change${NAMESPACE}`,
                    );
                }
            }


            /*
             * Destroy Select2 and restore the original
             * Django <select>.
             */
            if (this.$element) {
                this.$element.off(NAMESPACE);

                if (
                    this.$element.hasClass(
                        "select2-hidden-accessible",
                    )
                ) {
                    this.$element.select2("destroy");
                }
            }

            this.$element = null;
        }
    }


    // ------------------------------------------------------------------
    // Registry
    // ------------------------------------------------------------------

    const instances =
        new WeakMap();


    function initialize(root = document) {
        if (!root) {
            return;
        }


        /*
         * root itself may be the select.
         */
        if (
            root instanceof HTMLSelectElement
            && root.matches(SELECTOR)
        ) {
            initializeElement(root);
        }


        /*
         * Elements inside root.
         */
        if (
            typeof root.querySelectorAll === "function"
        ) {
            root
                .querySelectorAll(SELECTOR)
                .forEach(initializeElement);
        }
    }


    function initializeElement(element) {
        if (instances.has(element)) {
            return;
        }

        const controller =
            new LookupController(element);

        /*
         * Only register successfully initialized
         * controllers.
         */
        if (controller.initialized) {
            instances.set(
                element,
                controller,
            );
        }
    }


    function destroy(root = document) {
        if (!root) {
            return;
        }

        const elements = [];


        /*
         * root itself may be the select.
         */
        if (
            root instanceof HTMLSelectElement
            && root.matches(SELECTOR)
        ) {
            elements.push(root);
        }


        /*
         * Elements inside root.
         */
        if (
            typeof root.querySelectorAll === "function"
        ) {
            elements.push(
                ...root.querySelectorAll(
                    SELECTOR,
                ),
            );
        }


        /*
         * De-duplicate in case root is also matched
         * by querySelectorAll in a custom DOM implementation.
         */
        const uniqueElements =
            [...new Set(elements)];

        for (const element of uniqueElements) {
            const controller =
                instances.get(element);

            if (!controller) {
                continue;
            }

            controller.destroy();

            instances.delete(element);
        }
    }


    // ------------------------------------------------------------------
    // Public API
    // ------------------------------------------------------------------

    window.DjangoSpice =
        window.DjangoSpice || {};

    window.DjangoSpice.Lookup = {
        initialize,

        destroy,

        get(element) {
            return instances.get(element)
                || null;
        },
    };


    // ------------------------------------------------------------------
    // Initial page
    // ------------------------------------------------------------------

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            () => initialize(),
            { once: true },
        );
    } else {
        initialize();
    }


    // ------------------------------------------------------------------
    // HTMX
    // ------------------------------------------------------------------

    document.addEventListener(
        "htmx:afterSwap",
        event => {
            initialize(
                event.target,
            );
        },
    );


    document.addEventListener(
        "htmx:oobAfterSwap",
        event => {
            initialize(
                event.target,
            );
        },
    );

})();