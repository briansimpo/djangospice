/**
 * SpiceUI - Lightweight, Framework-Agnostic Vanilla JS UI Library
 * Designed for server-rendered templates (Django/Jinja/Rails) and HTMX.
 */
class SpiceUI {
    constructor() {
        this.activeModals = [];
        this.activeOffcanvas = null;
        this.activeSidebar = null;
        this.activeTooltip = null;
        this.activePopover = null;

        this.initStates();
        this.initListeners();
        this.initTabsFromHash();
    }

    /**
     * Enforces initial hidden/closed states across components unless explicitly 
     * overridden via `data-open="true"`. If `data-open="false"` or omitted, they stay closed.
     */
    initStates() {
        // Helper to evaluate boolean data-open attribute strictly
        const shouldBeOpen = (el) => el.dataset.open === 'true';

        // 1. Dropdowns / Collapses / Content wrappers
        const collapsibleSelectors = '[data-dropdown-menu], [data-collapse-content]';
        document.querySelectorAll(collapsibleSelectors).forEach(el => {
            if (shouldBeOpen(el)) {
                el.classList.remove('hidden');
                // Sync aria-expanded / chevrons if toggle exists nearby
                const wrapper = el.closest('[data-dropdown-wrapper]') || el.parentElement;
                const toggle = wrapper?.querySelector('[data-toggle="dropdown"], [data-toggle="collapse"]');
                if (toggle) {
                    toggle.setAttribute('aria-expanded', 'true');
                    const chevron = toggle.querySelector('[data-chevron]');
                    if (chevron) chevron.classList.add('rotate-180');
                }
            } else {
                el.classList.add('hidden');
            }
        });

        // 2. Modals
        document.querySelectorAll('[data-modal]').forEach(modal => {
            if (shouldBeOpen(modal)) {
                this.showModalElement(modal);
            } else {
                modal.classList.add('hidden');
                modal.setAttribute('aria-hidden', 'true');
            }
        });

        // 3. Offcanvas Drawers
        document.querySelectorAll('[data-offcanvas]').forEach(offcanvas => {
            if (shouldBeOpen(offcanvas)) {
                // If explicitly set to open on init
                const panel = offcanvas.querySelector('[data-offcanvas-panel]');
                const backdrop = offcanvas.querySelector('[data-offcanvas-backdrop]');
                offcanvas.classList.remove('pointer-events-none');
                offcanvas.setAttribute('aria-hidden', 'false');
                if (panel) panel.classList.remove('translate-x-full', '-translate-x-full', 'translate-y-full', '-translate-y-full');
                if (backdrop) backdrop.classList.remove('opacity-0');
                document.body.classList.add('overflow-hidden');
                this.activeOffcanvas = offcanvas;
            } else {
                offcanvas.classList.add('pointer-events-none');
                offcanvas.setAttribute('aria-hidden', 'true');
                const panel = offcanvas.querySelector('[data-offcanvas-panel]');
                const backdrop = offcanvas.querySelector('[data-offcanvas-backdrop]');
                
                const placement = offcanvas.dataset.placement || 'right';
                const translateMap = {
                    right: 'translate-x-full',
                    left: '-translate-x-full',
                    top: '-translate-y-full',
                    bottom: 'translate-y-full'
                };
                if (panel) panel.classList.add(translateMap[placement] || 'translate-x-full');
                if (backdrop) backdrop.classList.add('opacity-0');
            }
        });

        // 4. Sidebars
        document.querySelectorAll('[data-sidebar], aside[id]').forEach(sidebar => {
            if (shouldBeOpen(sidebar)) {
                sidebar.classList.remove('-translate-x-full');
                sidebar.classList.add('translate-x-0');
                this.activeSidebar = sidebar;
            } else {
                sidebar.classList.remove('translate-x-0');
                sidebar.classList.add('-translate-x-full');
            }
        });

        // 5. Server-rendered Toasts / Alerts initialization
        document.querySelectorAll('[data-toast]').forEach(toast => {
            requestAnimationFrame(() => {
                toast.classList.remove('translate-y-2', 'translate-y-4', 'opacity-0');
            });
            const duration = parseInt(toast.dataset.duration, 10) || 5000;
            if (duration > 0 && !toast.dataset.timer) {
                toast.dataset.timer = setTimeout(() => this.removeToast(toast), duration);
            }
        });
    }

    initListeners() {
        // =====================================================================
        // 1. GLOBAL CLICK DELEGATION
        // =====================================================================
        document.addEventListener('click', (e) => {
            // Close Dropdowns when clicking outside
            const dropdownToggle = e.target.closest('[data-toggle="dropdown"]');
            if (!dropdownToggle) {
                this.closeAllDropdowns(e.target);
            }

            // Close Popovers when clicking outside
            const popoverToggle = e.target.closest('[data-toggle="popover"]');
            if (!popoverToggle && this.activePopover && !this.activePopover.contains(e.target)) {
                this.hidePopover();
            }

            // Dismiss Sidebar via Backdrop Click
            if (e.target.matches('[data-sidebar-backdrop]') && this.activeSidebar) {
                this.closeSidebar(this.activeSidebar);
                return;
            }

            // Dismiss Modal via [data-dismiss="modal"]
            const dismissModalBtn = e.target.closest('[data-dismiss="modal"]');
            if (dismissModalBtn) {
                e.preventDefault();
                const modal = dismissModalBtn.closest('[data-modal]');
                if (modal) this.closeModal(modal);
                return;
            }

            // Dismiss Modal via Backdrop Click
            if (e.target.matches('[data-modal]:not([data-backdrop="static"])')) {
                if (!e.target.closest('[data-modal-dialog]') || e.target.hasAttribute('data-modal')) {
                    this.closeModal(e.target);
                    return;
                }
            }

            // Dismiss Offcanvas via [data-dismiss="offcanvas"]
            const dismissOffcanvasBtn = e.target.closest('[data-dismiss="offcanvas"]');
            if (dismissOffcanvasBtn) {
                e.preventDefault();
                const offcanvas = dismissOffcanvasBtn.closest('[data-offcanvas]');
                if (offcanvas) this.closeOffcanvas(offcanvas);
                return;
            }

            // Dismiss Offcanvas via Backdrop Click
            if (e.target.matches('[data-offcanvas-backdrop]') && this.activeOffcanvas) {
                if (this.activeOffcanvas.dataset.backdrop !== 'static') {
                    this.closeOffcanvas(this.activeOffcanvas);
                }
                return;
            }

            // Dismiss Toast
            const dismissToastBtn = e.target.closest('[data-dismiss="toast"]');
            if (dismissToastBtn) {
                e.preventDefault();
                const toast = dismissToastBtn.closest('[data-toast]');
                if (toast) this.removeToast(toast);
                return;
            }

            // Dismiss Alert
            const dismissAlertBtn = e.target.closest('[data-dismiss="alert"]');
            if (dismissAlertBtn) {
                e.preventDefault();
                const alert = dismissAlertBtn.closest('[data-alert]');
                if (alert) {
                    alert.classList.add('opacity-0', 'scale-95', 'transition-all', 'duration-150');
                    setTimeout(() => alert.remove(), 150);
                }
                return;
            }

            // Route Declarative Toggles ([data-toggle])
            const toggle = e.target.closest('[data-toggle]');
            if (!toggle) return;

            const type = toggle.dataset.toggle;
            if (type === 'sidebar') this.handleSidebar(toggle, e);
            if (type === 'dropdown') this.handleDropdown(toggle, e);
            if (type === 'modal') this.openModal(toggle, e);
            if (type === 'offcanvas') this.openOffcanvas(toggle, e);
            if (type === 'tab') this.activateTab(toggle, e);
            if (type === 'collapse') this.handleCollapse(toggle, e);
            if (type === 'popover') this.togglePopover(toggle, e);
        });

        // =====================================================================
        // 2. HOVER & FOCUS DELEGATION (TOOLTIPS)
        // =====================================================================
        document.addEventListener('mouseover', (e) => this.handleTooltipShow(e));
        document.addEventListener('mouseout', (e) => this.handleTooltipHide(e));
        document.addEventListener('focusin', (e) => this.handleTooltipShow(e));
        document.addEventListener('focusout', (e) => this.handleTooltipHide(e));

        // =====================================================================
        // 3. GLOBAL KEYBOARD ACCESSIBILITY (ESCAPE & FOCUS TRAP)
        // =====================================================================
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllDropdowns();
                this.hidePopover();

                if (this.activeSidebar) {
                    this.closeSidebar(this.activeSidebar);
                    return;
                }

                if (this.activeOffcanvas && this.activeOffcanvas.dataset.keyboard !== 'false') {
                    this.closeOffcanvas(this.activeOffcanvas);
                    return;
                }

                if (this.activeModals.length > 0) {
                    const topModal = this.activeModals[this.activeModals.length - 1];
                    if (topModal.dataset.keyboard !== 'false') {
                        this.closeModal(topModal);
                    }
                }
            }

            if (e.key === 'Tab' && this.activeModals.length > 0) {
                const topModal = this.activeModals[this.activeModals.length - 1];
                this.trapFocus(topModal, e);
            }
        });

        // =====================================================================
        // 4. HTMX LIFECYCLE INTEGRATION
        // =====================================================================
        document.addEventListener('htmx:afterSwap', (e) => {
            const modal = e.target.closest('[data-modal]') || e.target.querySelector('[data-modal]');
            if (modal && modal.dataset.autoOpen === 'true') {
                this.showModalElement(modal);
            }
            this.initStates();
        });
    }

    // =========================================================================
    // SIDEBAR MANAGEMENT
    // =========================================================================

    handleSidebar(toggle, e) {
        if (e) e.preventDefault();
        e.stopPropagation();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');
        const sidebar = document.querySelector(targetSelector);
        if (!sidebar) return;

        const isOpen = sidebar.classList.contains('translate-x-0');
        if (isOpen) {
            this.closeSidebar(sidebar);
        } else {
            this.openSidebar(sidebar, toggle);
        }
    }

    openSidebar(sidebar, toggle = null) {
        sidebar.__triggerElement = toggle;
        sidebar.classList.remove('-translate-x-full');
        sidebar.classList.add('translate-x-0');

        let backdrop = document.querySelector('#spice-sidebar-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.id = 'spice-sidebar-backdrop';
            backdrop.className = 'fixed inset-0 z-30 bg-black/30 lg:hidden pt-16 transition-opacity opacity-0';
            backdrop.setAttribute('data-sidebar-backdrop', '');
            document.body.appendChild(backdrop);
            requestAnimationFrame(() => backdrop.classList.remove('opacity-0'));
        } else {
            backdrop.classList.remove('hidden');
            requestAnimationFrame(() => backdrop.classList.remove('opacity-0'));
        }

        this.activeSidebar = sidebar;
        sidebar.dispatchEvent(new CustomEvent('spice:sidebar:shown', { bubbles: true }));
    }

    closeSidebar(sidebar = null) {
        const targetSidebar = sidebar || this.activeSidebar;
        if (!targetSidebar) return;

        targetSidebar.classList.remove('translate-x-0');
        targetSidebar.classList.add('-translate-x-full');

        const backdrop = document.querySelector('#spice-sidebar-backdrop');
        if (backdrop) {
            backdrop.classList.add('opacity-0');
            setTimeout(() => backdrop.classList.add('hidden'), 200);
        }

        if (targetSidebar.__triggerElement && document.body.contains(targetSidebar.__triggerElement)) {
            targetSidebar.__triggerElement.focus();
        }

        this.activeSidebar = null;
        targetSidebar.dispatchEvent(new CustomEvent('spice:sidebar:hidden', { bubbles: true }));
    }

    // =========================================================================
    // TOAST NOTIFICATIONS (spice.showToast)
    // =========================================================================

    showToast({ title = '', message = '', type = 'info', duration = 4000 } = {}) {
        let container = document.querySelector('#spice-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'spice-toast-container';
            container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-3 pointer-events-none max-w-sm w-full px-4';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.setAttribute('data-toast', '');
        toast.setAttribute('role', 'status');

        const variants = {
            success: 'border-emerald-200 bg-emerald-50/95 text-emerald-900',
            error: 'border-rose-200 bg-rose-50/95 text-rose-900',
            warning: 'border-amber-200 bg-amber-50/95 text-amber-900',
            info: 'border-slate-200 bg-white/95 text-slate-800'
        };

        const icons = {
            success: '<i class="fa-solid fa-circle-check text-emerald-600 mt-0.5"></i>',
            error: '<i class="fa-solid fa-circle-exclamation text-rose-600 mt-0.5"></i>',
            warning: '<i class="fa-solid fa-triangle-exclamation text-amber-600 mt-0.5"></i>',
            info: '<i class="fa-solid fa-circle-info text-blue-600 mt-0.5"></i>'
        };

        toast.className = `pointer-events-auto flex items-start gap-3 p-4 rounded-xl shadow-xl border backdrop-blur-sm transition-all transform translate-y-2 opacity-0 duration-200 ${variants[type] || variants.info}`;

        toast.innerHTML = `
            ${icons[type] || icons.info}
            <div class="flex-1">
                ${title ? `<h4 class="text-sm font-bold mb-0.5">${title}</h4>` : ''}
                <p class="text-xs leading-relaxed">${message}</p>
            </div>
            <button type="button" data-dismiss="toast" aria-label="Close" class="text-slate-400 hover:text-slate-600 transition-colors">
                <i class="fa-solid fa-xmark text-xs"></i>
            </button>
        `;

        container.appendChild(toast);
        requestAnimationFrame(() => toast.classList.remove('translate-y-2', 'opacity-0'));

        if (duration > 0) {
            toast.dataset.timer = setTimeout(() => this.removeToast(toast), duration);
        }

        return toast;
    }

    removeToast(toast) {
        if (!toast) return;
        if (toast.dataset.timer) clearTimeout(parseInt(toast.dataset.timer, 10));
        toast.classList.add('translate-y-2', 'opacity-0');
        setTimeout(() => toast.remove(), 200);
    }

    // =========================================================================
    // DROPDOWNS
    // =========================================================================

    handleDropdown(toggle, e) {
        e.preventDefault();
        e.stopPropagation();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');
        const dropdown = (targetSelector && targetSelector !== '#')
            ? document.querySelector(targetSelector)
            : toggle.nextElementSibling;

        if (!dropdown) return;

        const isOpen = !dropdown.classList.contains('hidden');
        this.closeAllDropdowns();

        if (!isOpen) {
            dropdown.classList.remove('hidden');
            toggle.setAttribute('aria-expanded', 'true');
            const chevron = toggle.querySelector('[data-chevron]');
            if (chevron) chevron.classList.add('rotate-180');
        }
    }

    closeAllDropdowns(exceptElement = null) {
        document.querySelectorAll('[data-dropdown-menu]').forEach(menu => {
            if (!exceptElement || !menu.contains(exceptElement)) {
                menu.classList.add('hidden');
                const wrapper = menu.closest('[data-dropdown-wrapper]') || menu.parentElement;
                const toggle = wrapper?.querySelector('[data-toggle="dropdown"]');
                if (toggle) {
                    toggle.setAttribute('aria-expanded', 'false');
                    const chevron = toggle.querySelector('[data-chevron]');
                    if (chevron) chevron.classList.remove('rotate-180');
                }
            }
        });
    }

    // =========================================================================
    // MODALS
    // =========================================================================

    openModal(toggle, e) {
        if (e) e.preventDefault();
        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');
        const modal = document.querySelector(targetSelector);
        if (!modal) return;

        modal.__triggerElement = toggle;
        this.showModalElement(modal);
    }

    showModalElement(modal) {
        if (this.activeModals.includes(modal)) return;

        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('overflow-hidden');

        this.activeModals.push(modal);

        const focusable = this.getFocusableElements(modal);
        if (focusable.length > 0) {
            const autoFocusEl = modal.querySelector('[autofocus]') || focusable[0];
            requestAnimationFrame(() => autoFocusEl.focus());
        }

        modal.dispatchEvent(new CustomEvent('spice:modal:shown', { bubbles: true }));
    }

    closeModal(modal) {
        if (!modal) return;

        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');

        this.activeModals = this.activeModals.filter(m => m !== modal);

        if (this.activeModals.length === 0 && !this.activeOffcanvas) {
            document.body.classList.remove('overflow-hidden');
        }

        if (modal.__triggerElement && document.body.contains(modal.__triggerElement)) {
            modal.__triggerElement.focus();
        }

        modal.dispatchEvent(new CustomEvent('spice:modal:hidden', { bubbles: true }));
    }

    getFocusableElements(container) {
        return Array.from(
            container.querySelectorAll(
                'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
        ).filter(el => el.offsetParent !== null);
    }

    trapFocus(modal, e) {
        const focusable = this.getFocusableElements(modal);
        if (focusable.length === 0) return;

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

    // =========================================================================
    // OFFCANVAS / DRAWERS
    // =========================================================================

    openOffcanvas(toggle, e) {
        if (e) e.preventDefault();
        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');
        const offcanvas = document.querySelector(targetSelector);
        if (!offcanvas) return;

        if (this.activeOffcanvas && this.activeOffcanvas !== offcanvas) {
            this.closeOffcanvas(this.activeOffcanvas);
        }

        offcanvas.__triggerElement = toggle;
        offcanvas.classList.remove('pointer-events-none');
        offcanvas.setAttribute('aria-hidden', 'false');

        const panel = offcanvas.querySelector('[data-offcanvas-panel]');
        const backdrop = offcanvas.querySelector('[data-offcanvas-backdrop]');

        requestAnimationFrame(() => {
            if (panel) {
                panel.classList.remove(
                    'translate-x-full',
                    '-translate-x-full',
                    'translate-x-[-100%]',
                    'translate-y-full',
                    '-translate-y-full',
                    'translate-y-[-100%]'
                );
            }
            if (backdrop) backdrop.classList.remove('opacity-0');
        });

        document.body.classList.add('overflow-hidden');
        this.activeOffcanvas = offcanvas;

        offcanvas.dispatchEvent(new CustomEvent('spice:offcanvas:shown', { bubbles: true }));
    }

    closeOffcanvas(offcanvas) {
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

        if (panel) panel.classList.add(translateMap[placement] || 'translate-x-full');
        if (backdrop) backdrop.classList.add('opacity-0');

        offcanvas.setAttribute('aria-hidden', 'true');

        setTimeout(() => {
            offcanvas.classList.add('pointer-events-none');
            if (this.activeModals.length === 0) {
                document.body.classList.remove('overflow-hidden');
            }
        }, 300);

        if (offcanvas.__triggerElement && document.body.contains(offcanvas.__triggerElement)) {
            offcanvas.__triggerElement.focus();
        }

        this.activeOffcanvas = null;
        offcanvas.dispatchEvent(new CustomEvent('spice:offcanvas:hidden', { bubbles: true }));
    }

    // =========================================================================
    // DYNAMIC TABS
    // =========================================================================

    activateTab(toggle, e) {
        if (e) e.preventDefault();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');
        const targetPane = document.querySelector(targetSelector);
        if (!targetPane) return;

        const tabList = toggle.closest('[role="tablist"], [data-tabs]');
        const paneContainer = targetPane.parentElement;

        if (tabList) {
            tabList.querySelectorAll('[data-toggle="tab"]').forEach(tab => {
                tab.setAttribute('aria-selected', 'false');
                tab.dataset.state = 'inactive';
            });
        }

        if (paneContainer) {
            Array.from(paneContainer.children).forEach(pane => {
                if (pane.hasAttribute('data-tab-pane')) {
                    pane.classList.add('hidden');
                    pane.dataset.state = 'inactive';
                }
            });
        }

        toggle.setAttribute('aria-selected', 'true');
        toggle.dataset.state = 'active';

        targetPane.classList.remove('hidden');
        targetPane.dataset.state = 'active';

        if (tabList && tabList.dataset.syncHash === 'true' && targetSelector.startsWith('#')) {
            history.replaceState(null, '', targetSelector);
        }

        toggle.dispatchEvent(new CustomEvent('spice:tab:shown', {
            bubbles: true,
            detail: { tab: toggle, pane: targetPane }
        }));
    }

    initTabsFromHash() {
        const hash = window.location.hash;
        if (!hash) return;

        const matchingTab = document.querySelector(
            `[data-toggle="tab"][data-target="${hash}"], [data-toggle="tab"][href="${hash}"]`
        );
        if (matchingTab) {
            this.activateTab(matchingTab);
        }
    }

    // =========================================================================
    // ACCORDIONS & COLLAPSES
    // =========================================================================

    handleCollapse(toggle, e) {
        e.preventDefault();
        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');
        const target = document.querySelector(targetSelector);
        if (!target) return;

        const accordionGroup = toggle.closest('[data-accordion]');
        const isExpanded = !target.classList.contains('hidden');

        if (accordionGroup && !isExpanded && accordionGroup.dataset.accordion === 'single') {
            accordionGroup.querySelectorAll('[data-collapse-content]').forEach(content => {
                content.classList.add('hidden');
            });
            accordionGroup.querySelectorAll('[data-toggle="collapse"]').forEach(btn => {
                btn.setAttribute('aria-expanded', 'false');
                const chevron = btn.querySelector('[data-chevron]');
                if (chevron) chevron.classList.remove('rotate-180');
            });
        }

        target.classList.toggle('hidden');
        toggle.setAttribute('aria-expanded', String(!isExpanded));

        const chevron = toggle.querySelector('[data-chevron]');
        if (chevron) chevron.classList.toggle('rotate-180', !isExpanded);
    }

    // =========================================================================
    // TOOLTIPS & POPOVERS
    // =========================================================================

    handleTooltipShow(e) {
        const target = e.target.closest('[data-tooltip]');
        if (!target) return;

        const content = target.dataset.tooltip;
        if (!content) return;

        let tooltipEl = document.querySelector('#spice-global-tooltip');
        if (!tooltipEl) {
            tooltipEl = document.createElement('div');
            tooltipEl.id = 'spice-global-tooltip';
            tooltipEl.role = 'tooltip';
            tooltipEl.className = 'fixed z-50 px-2.5 py-1.5 text-xs font-medium text-white bg-slate-900 rounded-lg shadow-lg pointer-events-none transition-opacity duration-150 opacity-0';
            document.body.appendChild(tooltipEl);
        }

        tooltipEl.textContent = content;
        tooltipEl.classList.remove('opacity-0');

        const rect = target.getBoundingClientRect();
        const tRect = tooltipEl.getBoundingClientRect();
        const placement = target.dataset.tooltipPlacement || 'top';

        let top = rect.top - tRect.height - 8;
        let left = rect.left + (rect.width / 2) - (tRect.width / 2);

        if (placement === 'bottom' || top < 8) {
            top = rect.bottom + 8;
        }

        left = Math.max(8, Math.min(left, window.innerWidth - tRect.width - 8));

        tooltipEl.style.top = `${top}px`;
        tooltipEl.style.left = `${left}px`;
        this.activeTooltip = tooltipEl;
    }

    handleTooltipHide(e) {
        const target = e.target.closest('[data-tooltip]');
        if (!target) return;

        const tooltipEl = document.querySelector('#spice-global-tooltip');
        if (tooltipEl) {
            tooltipEl.classList.add('opacity-0');
        }
    }

    togglePopover(toggle, e) {
        e.preventDefault();
        e.stopPropagation();

        if (this.activePopover && this.activePopover.__trigger === toggle) {
            this.hidePopover();
            return;
        }

        this.hidePopover();

        const title = toggle.dataset.popoverTitle || '';
        const content = toggle.dataset.popoverContent || toggle.dataset.popover || '';
        if (!title && !content) return;

        const popover = document.createElement('div');
        popover.id = 'spice-global-popover';
        popover.__trigger = toggle;
        popover.className = 'fixed z-50 w-64 rounded-xl border border-slate-200 bg-white p-3.5 shadow-xl text-sm transition-opacity duration-150';

        popover.innerHTML = `
            ${title ? `<div class="font-bold text-slate-900 mb-1 pb-1.5 border-b border-slate-100">${title}</div>` : ''}
            <div class="text-xs text-slate-600 leading-relaxed">${content}</div>
        `;

        document.body.appendChild(popover);

        const rect = toggle.getBoundingClientRect();
        const pRect = popover.getBoundingClientRect();

        let top = rect.bottom + 8;
        let left = rect.left + (rect.width / 2) - (pRect.width / 2);

        if (top + pRect.height > window.innerHeight - 8) {
            top = rect.top - pRect.height - 8;
        }
        left = Math.max(8, Math.min(left, window.innerWidth - pRect.width - 8));

        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
        this.activePopover = popover;
    }

    hidePopover() {
        if (this.activePopover) {
            this.activePopover.remove();
            this.activePopover = null;
        }
    }
}

// Initialize global `spice` instance on page load
document.addEventListener('DOMContentLoaded', () => {
    window.spice = new SpiceUI();
});