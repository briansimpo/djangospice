
export class Modal {

    constructor() {
        this.activeModals = [];
    }

    /**
     * Initialize modal component.
     */
    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
        document.addEventListener('keydown', this.handleKeydown);
    }

    /**
     * Initialize modal states.
     */
    initStates(root = document) {
        root.querySelectorAll('[data-modal]').forEach(modal => {
            if (modal.dataset.open === 'true') {
                this.show(modal);
            } else {
                modal.classList.add('hidden');
                modal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    /**
     * Handle modal interactions.
     */
    handleClick = (e) => {

        // Modal toggle
        const toggle = e.target.closest('[data-toggle="modal"]');

        if (toggle) {
            this.open(toggle, e);
            return;
        }

        // Modal dismiss
        const dismiss = e.target.closest('[data-dismiss="modal"]');

        if (dismiss) {
            e.preventDefault();

            const modal = dismiss.closest('[data-modal]');

            if (modal) this.close(modal);

            return;
        }

        // Modal backdrop click
        if (
            e.target.matches('[data-modal]') &&
            e.target.dataset.backdrop !== 'static'
        ) {
            this.close(e.target);
        }
    };

    /**
     * Handle keyboard interactions.
     */
    handleKeydown = (e) => {
        if (e.key === 'Escape') {
            this.closeTopModal();
            return;
        }

        if (e.key === 'Tab') {
            this.trapFocus(e);
        }
    };

    /**
     * Open a modal using its trigger.
     */
    open(toggle, e) {
        if (e) e.preventDefault();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');

        if (!targetSelector || targetSelector === '#') return;

        let modal;

        try {
            modal = document.querySelector(targetSelector);
        } catch {
            return;
        }

        if (!modal) return;

        modal.__triggerElement = toggle;

        this.show(modal);
    }

    /**
     * Show a modal.
     */
    show(modal) {
        if (!modal || this.activeModals.includes(modal)) return;

        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');

        document.body.classList.add('overflow-hidden');

        this.activeModals.push(modal);

        const focusable = this.getFocusableElements(modal);

        if (focusable.length > 0) {
            const autoFocusEl = modal.querySelector('[autofocus]') || focusable[0];

            requestAnimationFrame(() => autoFocusEl.focus());
        }

        modal.dispatchEvent(
            new CustomEvent('spice:modal:shown', { bubbles: true })
        );
    }

    /**
     * Close a modal.
     */
    close(modal) {
        if (!modal || !this.activeModals.includes(modal)) return;

        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');

        this.activeModals = this.activeModals.filter(m => m !== modal);

        if (this.activeModals.length === 0) {
            document.body.classList.remove('overflow-hidden');
        }

        if (
            modal.__triggerElement &&
            document.body.contains(modal.__triggerElement)
        ) {
            modal.__triggerElement.focus();
        }

        modal.dispatchEvent(
            new CustomEvent('spice:modal:hidden', { bubbles: true })
        );
    }

    /**
     * Close the topmost modal.
     */
    closeTopModal() {
        if (this.activeModals.length === 0) return false;

        const topModal = this.activeModals[this.activeModals.length - 1];

        if (topModal.dataset.keyboard === 'false') return false;

        this.close(topModal);

        return true;
    }

    /**
     * Trap keyboard focus inside the active modal.
     */
    trapFocus(e) {
        if (this.activeModals.length === 0) return;

        const topModal = this.activeModals[this.activeModals.length - 1];
        const focusable = this.getFocusableElements(topModal);

        if (focusable.length === 0) {
            e.preventDefault();
            topModal.focus();
            return;
        }

        const firstEl = focusable[0];
        const lastEl = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === firstEl) {
            e.preventDefault();
            lastEl.focus();
        } else if (!e.shiftKey && document.activeElement === lastEl) {
            e.preventDefault();
            firstEl.focus();
        }
    }

    /**
     * Get focusable elements inside a container.
     */
    getFocusableElements(container) {
        return Array.from(
            container.querySelectorAll(
                'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
        ).filter(el => el.offsetParent !== null);
    }

    /**
     * Destroy component listeners.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);
        document.removeEventListener('keydown', this.handleKeydown);

        this.activeModals.forEach(modal => {
            modal.classList.add('hidden');
            modal.setAttribute('aria-hidden', 'true');
        });

        this.activeModals = [];

        document.body.classList.remove('overflow-hidden');
    }
}
