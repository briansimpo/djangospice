/**
 * SpiceTable - Dedicated table controller handling row selection,
 * bulk action state synchronization, and dynamic [id] context menu bindings.
 */
class SpiceTable {
    constructor(element) {
        this.el = element;
        this.selected = new Set();

        this.contextMenu = {
            x: 0,
            y: 0,
            recordId: null
        };

        this.init();
    }

    init() {
        // =====================================================================
        // CLICK DELEGATION (Context Menu Cleanup & Selection Actions)
        // =====================================================================
        this.el.addEventListener('click', (e) => {
            // Close context menu on outside click
            if (!e.target.closest('[data-context-menu]')) {
                this.closeContextMenu();
            }

            const actionEl = e.target.closest('[data-action]');
            if (!actionEl) return;

            const action = actionEl.dataset.action;
            if (action === 'clear-selection') this.clearSelection();
        });

        // =====================================================================
        // RIGHT-CLICK CONTEXT MENU DELEGATION
        // =====================================================================
        this.el.addEventListener('contextmenu', (e) => {
            const row = e.target.closest('[data-table-row]');
            if (row) {
                e.preventDefault();
                const recordId = row.dataset.objectId;
                this.openContextMenu(e, recordId);
            }
        });

        // =====================================================================
        // ROW & HEADER CHECKBOX SELECTION
        // =====================================================================
        this.el.addEventListener('change', (e) => {
            const actionEl = e.target.closest('[data-action]');
            if (!actionEl) return;

            const action = actionEl.dataset.action;
            if (action === 'toggle-all') {
                this.toggleAll(actionEl.checked);
            } else if (action === 'toggle-row') {
                this.toggleRow(actionEl.value, actionEl.checked);
            }
        });

        // =====================================================================
        // GLOBAL WINDOW LISTENERS (Escape & Scroll Cleanup)
        // =====================================================================
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeContextMenu();
            }
        });

        window.addEventListener('scroll', () => {
            this.closeContextMenu();
        }, { passive: true });

        this.syncState();
    }

    // =========================================================================
    // CONTEXT MENU & [id] PLACEHOLDER RESOLUTION
    // =========================================================================

    openContextMenu(event, id) {
        const width = 224;
        const height = 260;

        this.contextMenu.recordId = id;
        this.contextMenu.x = Math.max(8, Math.min(event.clientX, window.innerWidth - width - 8));
        this.contextMenu.y = Math.max(8, Math.min(event.clientY, window.innerHeight - height - 8));

        const menuEl = this.el.querySelector('[data-context-menu]');
        if (menuEl) {
            menuEl.dataset.activeRecordId = id;
            menuEl.style.left = `${this.contextMenu.x}px`;
            menuEl.style.top = `${this.contextMenu.y}px`;
            menuEl.classList.remove('hidden');

            menuEl.querySelectorAll('a, button').forEach(el => {
                const targetAttrs = ['hx-get', 'hx-post', 'hx-delete', 'hx-patch', 'hx-put', 'href'];

                targetAttrs.forEach(attr => {
                    if (el.hasAttribute(attr)) {
                        const originalAttrKey = `data-original-${attr.replace('-', '')}`;
                        if (!el.hasAttribute(originalAttrKey)) {
                            el.setAttribute(originalAttrKey, el.getAttribute(attr));
                        }

                        const template = el.getAttribute(originalAttrKey);
                        const resolvedUrl = template.replaceAll('[id]', id);
                        el.setAttribute(attr, resolvedUrl);
                    }
                });

                if (window.htmx) {
                    htmx.process(el);
                }
            });
        }
    }

    closeContextMenu() {
        const menuEl = this.el.querySelector('[data-context-menu]');
        if (menuEl) {
            menuEl.classList.add('hidden');
        }
    }

    // =========================================================================
    // SELECTION & STATE SYNC
    // =========================================================================

    toggleAll(checked) {
        const checkboxes = this.el.querySelectorAll('[data-row-checkbox]');
        checkboxes.forEach(cb => {
            cb.checked = checked;
            if (checked) {
                this.selected.add(cb.value);
            } else {
                this.selected.delete(cb.value);
            }
        });
        this.syncState();
    }

    toggleRow(id, checked) {
        if (checked) {
            this.selected.add(id);
        } else {
            this.selected.delete(id);
        }
        this.syncHeaderCheckbox();
        this.syncState();
    }

    clearSelection() {
        this.selected.clear();
        this.el.querySelectorAll('[data-row-checkbox]').forEach(cb => {
            cb.checked = false;
        });
        const selectAll = this.el.querySelector('[data-action="toggle-all"]');
        if (selectAll) selectAll.checked = false;
        this.syncState();
    }

    syncHeaderCheckbox() {
        const selectAll = this.el.querySelector('[data-action="toggle-all"]');
        const checkboxes = Array.from(this.el.querySelectorAll('[data-row-checkbox]'));
        if (selectAll && checkboxes.length > 0) {
            selectAll.checked = checkboxes.every(cb => cb.checked);
        }
    }

    syncState() {
        const count = this.selected.size;

        const countEl = this.el.querySelector('[data-selected-count]');
        if (countEl) countEl.textContent = count;

        const bulkBar = this.el.querySelector('[data-bulk-actions]');
        if (bulkBar) {
            bulkBar.classList.toggle('hidden', count === 0);
            
            if (count === 0) {
                const bulkDropdown = bulkBar.querySelector('[data-dropdown-menu]');
                if (bulkDropdown && !bulkDropdown.classList.contains('hidden')) {
                    bulkDropdown.classList.add('hidden');
                }
            }
        }

        const container = this.el.querySelector('[data-hidden-inputs]');
        if (container) {
            container.innerHTML = '';
            this.selected.forEach(id => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = container.dataset.paramName || 'selected_objects';
                input.value = id;
                container.appendChild(input);
            });
        }
    }
}

// =============================================================================
// AUTO-INITIALIZATION
// =============================================================================
function initTableComponents() {
    document.querySelectorAll('[data-table]').forEach(el => {
        if (!el.__tableInstance) {
            el.__tableInstance = new SpiceTable(el);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => initTableComponents());
document.addEventListener('htmx:afterSwap', () => initTableComponents());