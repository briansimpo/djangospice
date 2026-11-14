
/**
 * SpiceTable - Dedicated table controller handling:
 * - Row selection and highlighting
 * - Bulk action state synchronization
 * - Select-all and indeterminate checkbox states
 * - Dynamic [id] context menu bindings
 * - HTMX table replacement compatibility
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
        // CLICK DELEGATION
        // =====================================================================
        this.el.addEventListener('click', (e) => {

            // Close context menu on outside click.
            if (!e.target.closest('[data-context-menu]')) {
                this.closeContextMenu();
            }

            // Handle explicit table actions.
            const actionEl = e.target.closest('[data-action]');

            if (actionEl) {
                const action = actionEl.dataset.action;

                if (action === 'clear-selection') {
                    this.clearSelection();
                }
            }

            // =====================================================================
            // ROW CLICK: NAVIGATION OR SELECTION
            // =====================================================================

            const row = e.target.closest('[data-table-row]');

            if (!row || !this.el.contains(row)) return;

            // Ignore clicks on interactive elements.
            if (e.target.closest('a, button, input, select, textarea, label, [data-no-row-select], [contenteditable="true"], [role="button"], [role="menuitem"]')) {
                return;
            }

            // If a row URL exists, navigate instead of selecting.
            const url = row.dataset.rowUrl;

            if (url) {
                const target = row.dataset.rowTarget || '_self';

                if (target === '_blank') {
                    window.open(url, '_blank', 'noopener');
                } else {
                    window.location.assign(url);
                }

                return;
            }

            // Otherwise, perform row selection.
            const checkbox = row.querySelector('[data-row-checkbox]');

            if (!checkbox || checkbox.disabled) return;

            checkbox.checked = !checkbox.checked;

            checkbox.dispatchEvent(
                new Event('change', { bubbles: true })
            );
        });

        // =====================================================================
        // RIGHT-CLICK CONTEXT MENU DELEGATION
        // =====================================================================
        this.el.addEventListener('contextmenu', (e) => {
            const row = e.target.closest('[data-table-row]');

            if (row && this.el.contains(row)) {
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
        // GLOBAL WINDOW LISTENERS
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

        this.contextMenu.x = Math.max(
            8,
            Math.min(event.clientX, window.innerWidth - width - 8)
        );

        this.contextMenu.y = Math.max(
            8,
            Math.min(event.clientY, window.innerHeight - height - 8)
        );

        const menuEl = this.el.querySelector('[data-context-menu]');

        if (menuEl) {
            menuEl.dataset.activeRecordId = id;

            menuEl.style.left = `${this.contextMenu.x}px`;
            menuEl.style.top = `${this.contextMenu.y}px`;

            menuEl.classList.remove('hidden');

            menuEl.querySelectorAll('a, button').forEach(el => {

                const targetAttrs = [
                    'hx-get',
                    'hx-post',
                    'hx-delete',
                    'hx-patch',
                    'hx-put',
                    'href'
                ];

                targetAttrs.forEach(attr => {

                    if (el.hasAttribute(attr)) {

                        const originalAttrKey =
                            `data-original-${attr.replace('-', '')}`;

                        if (!el.hasAttribute(originalAttrKey)) {
                            el.setAttribute(
                                originalAttrKey,
                                el.getAttribute(attr)
                            );
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
    // SELECTION & STATE SYNCHRONIZATION
    // =========================================================================

    toggleAll(checked) {
        const checkboxes = this.el.querySelectorAll(
            '[data-row-checkbox]:not(:disabled)'
        );

        checkboxes.forEach(cb => {

            cb.checked = checked;

            if (checked) {
                this.selected.add(cb.value);
            } else {
                this.selected.delete(cb.value);
            }

            this.syncRow(cb);
        });

        this.syncHeaderCheckbox();
        this.syncState();
    }

    toggleRow(id, checked) {

        if (checked) {
            this.selected.add(id);
        } else {
            this.selected.delete(id);
        }

        const checkbox = Array.from(
            this.el.querySelectorAll('[data-row-checkbox]')
        ).find(cb => cb.value === id);

        if (checkbox) {
            this.syncRow(checkbox);
        }

        this.syncHeaderCheckbox();
        this.syncState();
    }

    /**
     * Synchronize checkbox state with row highlighting.
     */
    syncRow(checkbox) {
        const row = checkbox.closest('[data-table-row]');

        if (!row) return;

        row.classList.toggle('is-selected', checkbox.checked);
    }

    /**
     * Synchronize header checkbox checked and indeterminate states.
     */
    syncHeaderCheckbox() {
        const selectAll = this.el.querySelector(
            '[data-action="toggle-all"]'
        );

        if (!selectAll) return;

        const checkboxes = Array.from(
            this.el.querySelectorAll(
                '[data-row-checkbox]:not(:disabled)'
            )
        );

        const selectedCount = checkboxes.filter(
            cb => cb.checked
        ).length;

        selectAll.checked =
            checkboxes.length > 0 &&
            selectedCount === checkboxes.length;

        selectAll.indeterminate =
            selectedCount > 0 &&
            selectedCount < checkboxes.length;
    }

    clearSelection() {
        this.selected.clear();

        this.el.querySelectorAll('[data-row-checkbox]').forEach(cb => {
            cb.checked = false;
            this.syncRow(cb);
        });

        const selectAll = this.el.querySelector(
            '[data-action="toggle-all"]'
        );

        if (selectAll) {
            selectAll.checked = false;
            selectAll.indeterminate = false;
        }

        this.syncState();
    }

    // =========================================================================
    // BULK ACTION STATE & HIDDEN INPUT SYNCHRONIZATION
    // =========================================================================

    syncState() {
        const count = this.selected.size;

        const countEl = this.el.querySelector('[data-selected-count]');

        if (countEl) {
            countEl.textContent = count;
        }

        const bulkBar = this.el.querySelector('[data-bulk-actions]');

        if (bulkBar) {
            bulkBar.classList.toggle('hidden', count === 0);

            if (count === 0) {
                const bulkDropdown = bulkBar.querySelector(
                    '[data-dropdown-menu]'
                );

                if (
                    bulkDropdown &&
                    !bulkDropdown.classList.contains('hidden')
                ) {
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
                input.name =
                    container.dataset.paramName || 'selected_objects';
                input.value = id;

                container.appendChild(input);
            });
        }

        this.syncHeaderCheckbox();
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

document.addEventListener('DOMContentLoaded', () => {
    initTableComponents();
});

document.addEventListener('htmx:afterSwap', () => {
    initTableComponents();
});
