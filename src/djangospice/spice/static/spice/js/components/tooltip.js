
export class TooltipPopover {
    constructor() {
        this.activeTooltip = null;
        this.activePopover = null;
        this.resizeFrame = null;
    }

    init() {
        document.addEventListener('mouseover', this.handleMouseOver);
        document.addEventListener('mouseout', this.handleMouseOut);
        document.addEventListener('focusin', this.handleFocusIn);
        document.addEventListener('focusout', this.handleFocusOut);
        document.addEventListener('click', this.handleClick);
        document.addEventListener('keydown', this.handleKeydown);

        window.addEventListener('resize', this.handleResize);
        window.addEventListener('scroll', this.handleScroll, true);
    }

    initStates() {
        // All interactions use delegated event listeners.
    }

    // ---------------------------------------------------------
    // Tooltip
    // ---------------------------------------------------------

    handleMouseOver = (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (!target || target.contains(e.relatedTarget)) return;

        this.showTooltip(target);
    };

    handleMouseOut = (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (!target || target.contains(e.relatedTarget)) return;

        this.hideTooltip(target);
    };

    handleFocusIn = (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (target) this.showTooltip(target);
    };

    handleFocusOut = (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (!target || target.contains(e.relatedTarget)) return;

        this.hideTooltip(target);
    };

    showTooltip(target) {
        const content = target.dataset.tooltip;
        if (!content) return;

        const tooltip = this.getTooltipElement();

        tooltip.textContent = content;
        tooltip.classList.remove('opacity-0');

        this.activeTooltip = tooltip;
        tooltip.__trigger = target;

        this.position(tooltip, target, target.dataset.tooltipPlacement || 'top');
    }

    getTooltipElement() {
        let tooltip = document.querySelector('#spice-global-tooltip');

        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'spice-global-tooltip';
            tooltip.setAttribute('role', 'tooltip');

            tooltip.className = [
                'fixed z-50 px-2.5 py-1.5',
                'text-xs font-medium text-white',
                'bg-slate-900 rounded-lg shadow-lg',
                'pointer-events-none transition-opacity duration-150',
                'opacity-0'
            ].join(' ');

            document.body.appendChild(tooltip);
        }

        return tooltip;
    }

    hideTooltip(target = null) {
        if (!this.activeTooltip) return;

        if (target && this.activeTooltip.__trigger !== target) return;

        this.activeTooltip.classList.add('opacity-0');
        this.activeTooltip = null;
    }

    // ---------------------------------------------------------
    // Popover
    // ---------------------------------------------------------

    handleClick = (e) => {
        const toggle = e.target.closest('[data-toggle="popover"]');

        if (toggle) {
            this.togglePopover(toggle, e);
            return;
        }

        if (
            this.activePopover &&
            !this.activePopover.contains(e.target) &&
            !this.activePopover.__trigger.contains(e.target)
        ) {
            this.hidePopover();
        }
    };

    togglePopover(toggle, e) {
        e.preventDefault();
        e.stopPropagation();

        if (this.activePopover?.__trigger === toggle) {
            this.hidePopover();
            return;
        }

        this.hidePopover();

        const popover = this.createPopover(toggle);
        if (!popover) return;

        document.body.appendChild(popover);

        this.activePopover = popover;

        toggle.setAttribute('aria-expanded', 'true');
        toggle.setAttribute('aria-controls', popover.id);

        this.position(
            popover,
            toggle,
            toggle.dataset.popoverPlacement || 'bottom'
        );

        popover.dispatchEvent(new CustomEvent('spice:popover:shown', {
            bubbles: true,
            detail: { trigger: toggle, popover }
        }));
    }

    createPopover(toggle) {
        const popover = document.createElement('div');

        popover.id = `spice-popover-${crypto.randomUUID()}`;
        popover.setAttribute('role', 'dialog');
        popover.setAttribute('aria-modal', 'false');

        popover.className = [
            'fixed z-50 w-64 max-w-[calc(100vw-1rem)]',
            'rounded-xl border border-slate-200',
            'bg-white p-3.5 shadow-xl text-sm',
            'transition-opacity duration-150'
        ].join(' ');

        const templateSelector = toggle.dataset.popoverTemplate;

        if (templateSelector) {
            let template;

            try {
                template = document.querySelector(templateSelector);
            } catch {
                return null;
            }

            if (!template || !(template instanceof HTMLTemplateElement)) {
                console.warn(`Popover template not found: ${templateSelector}`);
                return null;
            }

            popover.appendChild(template.content.cloneNode(true));
        } else {
            this.createSimpleContent(popover, toggle);
        }

        if (!popover.hasChildNodes()) return null;

        popover.__trigger = toggle;

        return popover;
    }

    createSimpleContent(popover, toggle) {
        const title = toggle.dataset.popoverTitle || '';
        const content =
            toggle.dataset.popoverContent ||
            toggle.dataset.popover ||
            '';

        if (title) {
            const heading = document.createElement('div');

            heading.className = [
                'font-bold text-slate-900 mb-1',
                'pb-1.5 border-b border-slate-100'
            ].join(' ');

            heading.textContent = title;
            popover.appendChild(heading);
        }

        if (content) {
            const body = document.createElement('div');

            body.className = 'text-xs text-slate-600 leading-relaxed';
            body.textContent = content;

            popover.appendChild(body);
        }
    }

    hidePopover() {
        if (!this.activePopover) return;

        const popover = this.activePopover;
        const trigger = popover.__trigger;

        if (trigger) {
            trigger.setAttribute('aria-expanded', 'false');
            trigger.removeAttribute('aria-controls');
        }

        popover.dispatchEvent(new CustomEvent('spice:popover:hidden', {
            bubbles: true,
            detail: { trigger, popover }
        }));

        popover.remove();
        this.activePopover = null;
    }

    // ---------------------------------------------------------
    // Positioning
    // ---------------------------------------------------------

    position(element, trigger, placement = 'bottom') {
        const rect = trigger.getBoundingClientRect();
        const elementRect = element.getBoundingClientRect();

        const gap = 8;
        const padding = 8;

        const placements = {
            top: {
                top: rect.top - elementRect.height - gap,
                left: rect.left + (rect.width - elementRect.width) / 2
            },
            bottom: {
                top: rect.bottom + gap,
                left: rect.left + (rect.width - elementRect.width) / 2
            },
            left: {
                top: rect.top + (rect.height - elementRect.height) / 2,
                left: rect.left - elementRect.width - gap
            },
            right: {
                top: rect.top + (rect.height - elementRect.height) / 2,
                left: rect.right + gap
            }
        };

        let position = placements[placement] || placements.bottom;

        // Flip vertically when necessary.
        if (
            position.top + elementRect.height > window.innerHeight - padding &&
            placement === 'bottom'
        ) {
            position = placements.top;
        } else if (position.top < padding && placement === 'top') {
            position = placements.bottom;
        }

        // Flip horizontally when necessary.
        if (position.left < padding && placement === 'left') {
            position = placements.right;
        } else if (
            position.left + elementRect.width > window.innerWidth - padding &&
            placement === 'right'
        ) {
            position = placements.left;
        }

        const maxLeft = Math.max(
            padding,
            window.innerWidth - elementRect.width - padding
        );

        const maxTop = Math.max(
            padding,
            window.innerHeight - elementRect.height - padding
        );

        element.style.top = `${Math.max(padding, Math.min(position.top, maxTop))}px`;
        element.style.left = `${Math.max(padding, Math.min(position.left, maxLeft))}px`;
    }

    handleResize = () => {
        this.scheduleReposition();
    };

    handleScroll = () => {
        this.scheduleReposition();
    };

    scheduleReposition() {
        if (this.resizeFrame) return;

        this.resizeFrame = requestAnimationFrame(() => {
            this.resizeFrame = null;

            if (this.activeTooltip?.__trigger?.isConnected) {
                this.position(
                    this.activeTooltip,
                    this.activeTooltip.__trigger,
                    this.activeTooltip.__trigger.dataset.tooltipPlacement || 'top'
                );
            }

            if (this.activePopover?.__trigger?.isConnected) {
                this.position(
                    this.activePopover,
                    this.activePopover.__trigger,
                    this.activePopover.__trigger.dataset.popoverPlacement || 'bottom'
                );
            }
        });
    }

    // ---------------------------------------------------------
    // Keyboard
    // ---------------------------------------------------------

    handleKeydown = (e) => {
        if (e.key !== 'Escape') return;

        this.hideTooltip();
        this.hidePopover();
    };

    // ---------------------------------------------------------
    // Lifecycle
    // ---------------------------------------------------------

    destroy() {
        document.removeEventListener('mouseover', this.handleMouseOver);
        document.removeEventListener('mouseout', this.handleMouseOut);
        document.removeEventListener('focusin', this.handleFocusIn);
        document.removeEventListener('focusout', this.handleFocusOut);
        document.removeEventListener('click', this.handleClick);
        document.removeEventListener('keydown', this.handleKeydown);

        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('scroll', this.handleScroll, true);

        if (this.resizeFrame) {
            cancelAnimationFrame(this.resizeFrame);
            this.resizeFrame = null;
        }

        this.hideTooltip();
        this.hidePopover();

        document.querySelector('#spice-global-tooltip')?.remove();
    }
}
