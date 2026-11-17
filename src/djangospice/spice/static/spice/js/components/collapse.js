
export class Collapse {

    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
    }

    /**
     * Initialize collapse elements.
     */
    initStates(root = document) {
        root.querySelectorAll('[data-collapse-content]').forEach(el => {
            if (el.dataset.open === 'true') {
                el.classList.remove('hidden');
                this.syncToggle(el, true);
            } else {
                el.classList.add('hidden');
                this.syncToggle(el, false);
            }
        });
    }

    /**
     * Handle collapse interactions.
     */
    handleClick = (e) => {
        const toggle = e.target.closest('[data-toggle="collapse"]');

        if (!toggle) return;

        e.preventDefault();
        this.toggle(toggle);
    };

    /**
     * Toggle collapse content.
     */
    toggle(toggle) {
        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');

        if (!targetSelector) return;

        let target;

        try {
            target = document.querySelector(targetSelector);
        } catch {
            return;
        }

        if (!target) return;

        const accordionGroup = toggle.closest('[data-accordion]');
        const isExpanded = !target.classList.contains('hidden');

        // Close other accordion items.
        if (
            accordionGroup &&
            !isExpanded &&
            accordionGroup.dataset.accordion === 'single'
        ) {
            accordionGroup.querySelectorAll('[data-collapse-content]').forEach(content => {
                content.classList.add('hidden');
                this.syncToggle(content, false);
            });
        }

        // Toggle target.
        target.classList.toggle('hidden');

        this.syncToggle(target, !isExpanded);
    }

    /**
     * Synchronize toggle accessibility and visual state.
     */
    syncToggle(target, isExpanded) {
        const wrapper = target.closest('[data-collapse-wrapper]') || target.parentElement;

        const toggle = wrapper?.querySelector('[data-toggle="collapse"]');

        if (!toggle) return;

        toggle.setAttribute('aria-expanded', String(isExpanded));

        const chevron = toggle.querySelector('[data-chevron]');

        if (chevron) {
            chevron.classList.toggle('rotate-180', isExpanded);
        }
    }

    /**
     * Remove event listeners.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);
    }
}
