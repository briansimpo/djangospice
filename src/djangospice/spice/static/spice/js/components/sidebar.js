
export class Sidebar {

    constructor() {
        this.activeSidebar = null;
        this.backdrop = null;
        this.closeTimer = null;
    }

    /**
     * Initialize sidebar component.
     */
    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
    }

    /**
     * Initialize sidebar states.
     */
    initStates(root = document) {
        root.querySelectorAll('[data-sidebar], aside[id]').forEach(sidebar => {
            if (sidebar.dataset.open === 'true') {
                this.show(sidebar);
            } else {
                this.hide(sidebar);
            }
        });
    }

    /**
     * Handle sidebar interactions.
     */
    handleClick = (e) => {

        // Sidebar toggle
        const toggle = e.target.closest('[data-toggle="sidebar"]');

        if (toggle) {
            this.handleToggle(toggle, e);
            return;
        }

        // Sidebar backdrop
        if (e.target.closest('[data-sidebar-backdrop]')) {
            this.close();
        }
    };

    /**
     * Handle sidebar toggle.
     */
    handleToggle(toggle, e) {
        e.preventDefault();
        e.stopPropagation();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');

        if (!targetSelector || targetSelector === '#') return;

        let sidebar;

        try {
            sidebar = document.querySelector(targetSelector);
        } catch {
            return;
        }

        if (!sidebar) return;

        if (this.activeSidebar === sidebar) {
            this.close(sidebar);
        } else {
            this.open(sidebar, toggle);
        }
    }

    /**
     * Open sidebar.
     */
    open(sidebar, toggle = null) {
        if (!sidebar) return;

        if (this.activeSidebar && this.activeSidebar !== sidebar) {
            this.close(this.activeSidebar);
        }

        sidebar.__triggerElement = toggle;

        this.show(sidebar);
    }

    /**
     * Show sidebar.
     */
    show(sidebar) {
        if (!sidebar) return;

        clearTimeout(this.closeTimer);

        sidebar.classList.remove('-translate-x-full');
        sidebar.classList.add('translate-x-0');

        this.activeSidebar = sidebar;

        this.showBackdrop();

        sidebar.dispatchEvent(
            new CustomEvent('spice:sidebar:shown', { bubbles: true })
        );
    }

    /**
     * Show or create sidebar backdrop.
     */
    showBackdrop() {
        let backdrop = document.querySelector('#spice-sidebar-backdrop');

        if (!backdrop) {
            backdrop = document.createElement('div');

            backdrop.id = 'spice-sidebar-backdrop';

            backdrop.className = [
                'fixed',
                'inset-0',
                'z-30',
                'bg-black/30',
                'lg:hidden',
                'pt-16',
                'transition-opacity',
                'opacity-0'
            ].join(' ');

            backdrop.setAttribute('data-sidebar-backdrop', '');

            document.body.appendChild(backdrop);
        } else {
            backdrop.classList.remove('hidden');
        }

        this.backdrop = backdrop;

        requestAnimationFrame(() => {
            backdrop.classList.remove('opacity-0');
        });
    }

    /**
     * Close sidebar.
     */
    close(sidebar = this.activeSidebar) {
        if (!sidebar || this.activeSidebar !== sidebar) return;

        sidebar.classList.remove('translate-x-0');
        sidebar.classList.add('-translate-x-full');

        this.hideBackdrop();

        if (
            sidebar.__triggerElement &&
            document.body.contains(sidebar.__triggerElement)
        ) {
            sidebar.__triggerElement.focus();
        }

        this.activeSidebar = null;

        sidebar.dispatchEvent(
            new CustomEvent('spice:sidebar:hidden', { bubbles: true })
        );
    }

    /**
     * Hide backdrop.
     */
    hideBackdrop() {
        if (!this.backdrop) return;

        const backdrop = this.backdrop;

        backdrop.classList.add('opacity-0');

        this.closeTimer = setTimeout(() => {
            if (this.activeSidebar) return;

            backdrop.classList.add('hidden');
        }, 200);
    }

    /**
     * Hide sidebar without animation events.
     */
    hide(sidebar) {
        if (!sidebar) return;

        sidebar.classList.remove('translate-x-0');
        sidebar.classList.add('-translate-x-full');

        if (this.activeSidebar === sidebar) {
            this.activeSidebar = null;
        }
    }

    /**
     * Destroy component listeners.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);

        clearTimeout(this.closeTimer);

        if (this.activeSidebar) {
            this.hide(this.activeSidebar);
        }

        if (this.backdrop) {
            this.backdrop.remove();
            this.backdrop = null;
        }

        this.activeSidebar = null;
    }
}
