import { Modal } from './components/modal.js';
import { Offcanvas } from './components/offcanvas.js';
import { Sidebar } from './components/sidebar.js';
import { Dropdown } from './components/dropdown.js';
import { Tabs } from './components/tabs.js';
import { Collapse } from './components/collapse.js';
import { TooltipPopover } from './components/tooltip.js';
import { Toast } from './components/toast.js';


export class SpiceUI {
    constructor() {
        this.components = {
            modal: new Modal(),
            offcanvas: new Offcanvas(),
            sidebar: new Sidebar(),
            dropdown: new Dropdown(),
            tabs: new Tabs(),
            collapse: new Collapse(),
            tooltipPopover: new TooltipPopover(),
            toast: new Toast(),
        };

        this.init();
    }

    /**
     * Initialize all components.
     */
    init() {
        Object.values(this.components).forEach(component => {
            component.init();
        });

        this.initListeners();
    }

    /**
     * Initialize dynamically inserted content.
     */
    initStates(root = document) {
        Object.values(this.components).forEach(component => {
            component.initStates?.(root);
        });
    }

    /**
     * Register global integrations.
     */
    initListeners() {
        document.addEventListener('htmx:afterSwap', this.handleAfterSwap);

        document.body.addEventListener('show-alert', this.handleShowAlert);
    }

    /**
     * Handle HTMX content updates.
     */
    handleAfterSwap = (e) => {
        const root = e.target;

        this.initStates(root);

        const modal = root.matches?.('[data-modal]')
            ? root
            : root.querySelector?.('[data-modal]');

        if (modal?.dataset.autoOpen === 'true') {
            this.components.modal.show(modal);
        }
    };

    /**
     * Handle programmatic toast notifications.
     */
    handleShowAlert = (event) => {
        this.components.toast.show(event.detail);
    };

    /**
     * Destroy all components and global listeners.
     */
    destroy() {
        document.removeEventListener('htmx:afterSwap', this.handleAfterSwap);

        document.body.removeEventListener('show-alert', this.handleShowAlert);

        Object.values(this.components).forEach(component => {
            component.destroy?.();
        });
    }
}
