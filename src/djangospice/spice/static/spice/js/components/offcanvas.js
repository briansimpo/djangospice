
export class Offcanvas {

    constructor() {
        this.activeOffcanvas = null;
        this.closeTimer = null;
    }

    /**
     * Initialize offcanvas component.
     */
    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
        document.addEventListener('keydown', this.handleKeydown);
    }

    /**
     * Initialize offcanvas states.
     */
    initStates(root = document) {
        root.querySelectorAll('[data-offcanvas]').forEach(offcanvas => {
            if (offcanvas.dataset.open === 'true') {
                this.show(offcanvas);
            } else {
                this.hide(offcanvas);
            }
        });
    }

    /**
     * Handle offcanvas interactions.
     */
    handleClick = (e) => {

        // Open offcanvas
        const toggle = e.target.closest('[data-toggle="offcanvas"]');

        if (toggle) {
            this.open(toggle, e);
            return;
        }

        // Dismiss offcanvas
        const dismiss = e.target.closest('[data-dismiss="offcanvas"]');

        if (dismiss) {
            e.preventDefault();

            const offcanvas = dismiss.closest('[data-offcanvas]');

            if (offcanvas) this.close(offcanvas);

            return;
        }

        // Backdrop click
        const backdrop = e.target.closest('[data-offcanvas-backdrop]');

        if (backdrop && this.activeOffcanvas) {
            if (this.activeOffcanvas.dataset.backdrop !== 'static') {
                this.close(this.activeOffcanvas);
            }
        }
    };

    /**
     * Handle keyboard interactions.
     */
    handleKeydown = (e) => {
        if (e.key === 'Escape' && this.activeOffcanvas) {
            if (this.activeOffcanvas.dataset.keyboard !== 'false') {
                this.close();
            }
        }
    };

    /**
     * Open offcanvas using its trigger.
     */
    open(toggle, e) {
        if (e) e.preventDefault();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');

        if (!targetSelector || targetSelector === '#') return;

        let offcanvas;

        try {
            offcanvas = document.querySelector(targetSelector);
        } catch {
            return;
        }

        if (!offcanvas) return;

        offcanvas.__triggerElement = toggle;

        this.show(offcanvas);
    }

    /**
     * Show offcanvas.
     */
    show(offcanvas) {
        if (!offcanvas || this.activeOffcanvas === offcanvas) return;

        if (this.activeOffcanvas) {
            this.close(this.activeOffcanvas);
        }

        clearTimeout(this.closeTimer);

        const panel = offcanvas.querySelector('[data-offcanvas-panel]');
        const backdrop = offcanvas.querySelector('[data-offcanvas-backdrop]');

        offcanvas.classList.remove('pointer-events-none');
        offcanvas.setAttribute('aria-hidden', 'false');

        document.body.classList.add('overflow-hidden');

        this.activeOffcanvas = offcanvas;

        requestAnimationFrame(() => {
            if (panel) {
                panel.classList.remove(
                    'translate-x-full',
                    '-translate-x-full',
                    'translate-y-full',
                    '-translate-y-full'
                );
            }

            if (backdrop) {
                backdrop.classList.remove('opacity-0');
            }
        });

        offcanvas.dispatchEvent(
            new CustomEvent('spice:offcanvas:shown', { bubbles: true })
        );
    }

    /**
     * Close offcanvas.
     */
    close(offcanvas = this.activeOffcanvas) {
        if (!offcanvas || this.activeOffcanvas !== offcanvas) return;

        const panel = offcanvas.querySelector('[data-offcanvas-panel]');
        const backdrop = offcanvas.querySelector('[data-offcanvas-backdrop]');

        const placement = offcanvas.dataset.placement || 'right';

        const translateMap = {
            right: 'translate-x-full',
            left: '-translate-x-full',
            top: '-translate-y-full',
            bottom: 'translate-y-full'
        };

        if (panel) {
            panel.classList.add(translateMap[placement] || 'translate-x-full');
        }

        if (backdrop) {
            backdrop.classList.add('opacity-0');
        }

        offcanvas.setAttribute('aria-hidden', 'true');

        this.activeOffcanvas = null;

        if (offcanvas.__triggerElement && document.body.contains(offcanvas.__triggerElement)) {
            offcanvas.__triggerElement.focus();
        }

        this.closeTimer = setTimeout(() => {
            offcanvas.classList.add('pointer-events-none');

            if (!this.activeOffcanvas) {
                document.body.classList.remove('overflow-hidden');
            }
        }, 300);

        offcanvas.dispatchEvent(
            new CustomEvent('spice:offcanvas:hidden', { bubbles: true })
        );
    }

    /**
     * Hide offcanvas without animation.
     */
    hide(offcanvas) {
        if (!offcanvas) return;

        const panel = offcanvas.querySelector('[data-offcanvas-panel]');
        const backdrop = offcanvas.querySelector('[data-offcanvas-backdrop]');

        const placement = offcanvas.dataset.placement || 'right';

        const translateMap = {
            right: 'translate-x-full',
            left: '-translate-x-full',
            top: '-translate-y-full',
            bottom: 'translate-y-full'
        };

        offcanvas.classList.add('pointer-events-none');
        offcanvas.setAttribute('aria-hidden', 'true');

        if (panel) {
            panel.classList.add(translateMap[placement] || 'translate-x-full');
        }

        if (backdrop) {
            backdrop.classList.add('opacity-0');
        }

        if (this.activeOffcanvas === offcanvas) {
            this.activeOffcanvas = null;
        }
    }

    /**
     * Destroy component listeners.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);
        document.removeEventListener('keydown', this.handleKeydown);

        clearTimeout(this.closeTimer);

        if (this.activeOffcanvas) {
            this.hide(this.activeOffcanvas);
        }

        document.body.classList.remove('overflow-hidden');
        this.activeOffcanvas = null;
    }
}
