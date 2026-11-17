
export class Dropdown {

    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
    }

    /**
     * Initialize dropdown states.
     */
    initStates(root = document) {
        root.querySelectorAll('[data-dropdown-menu]').forEach(menu => {
            if (menu.dataset.open === 'true') {
                menu.classList.remove('hidden');
                this.syncToggle(menu, true);
            } else {
                menu.classList.add('hidden');
                this.syncToggle(menu, false);
            }
        });
    }

    /**
     * Handle dropdown interactions.
     */
    handleClick = (e) => {
        const toggle = e.target.closest('[data-toggle="dropdown"]');

        if (toggle) {
            this.toggle(toggle, e);
            return;
        }

        // Close dropdowns when clicking outside.
        this.closeAll(e.target);
    };

    /**
     * Toggle dropdown visibility.
     */
    toggle(toggle, e) {
        e.preventDefault();
        e.stopPropagation();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');

        const dropdown = (targetSelector && targetSelector !== '#')
            ? document.querySelector(targetSelector)
            : toggle.nextElementSibling;

        if (!dropdown) return;

        const isOpen = !dropdown.classList.contains('hidden');

        this.closeAll();

        if (!isOpen) {
            dropdown.classList.remove('hidden');
            this.syncToggle(dropdown, true);
        }
    }

    /**
     * Close all dropdowns except the one containing the given element.
     */
    closeAll(exceptElement = null) {
        document.querySelectorAll('[data-dropdown-menu]').forEach(menu => {
            if (!exceptElement || !menu.contains(exceptElement)) {
                menu.classList.add('hidden');
                this.syncToggle(menu, false);
            }
        });
    }

    /**
     * Synchronize toggle accessibility and visual state.
     */
    syncToggle(menu, isOpen) {
        const wrapper = menu.closest('[data-dropdown-wrapper]') || menu.parentElement;

        const toggle = wrapper?.querySelector('[data-toggle="dropdown"]');

        if (!toggle) return;

        toggle.setAttribute('aria-expanded', String(isOpen));

        const chevron = toggle.querySelector('[data-chevron]');

        if (chevron) {
            chevron.classList.toggle('rotate-180', isOpen);
        }
    }

    /**
     * Remove event listeners.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);
    }
}
