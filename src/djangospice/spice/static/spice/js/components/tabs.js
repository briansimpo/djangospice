
export class Tabs {

    /**
     * Initialize tabs component.
     */
    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
        window.addEventListener('hashchange', this.handleHashChange);

        this.initFromHash();
    }

    /**
     * Initialize tab states.
     */
    initStates(root = document) {
        const tabLists = [];

        if (root.matches?.('[role="tablist"], [data-tabs]')) {
            tabLists.push(root);
        }

        tabLists.push(
            ...root.querySelectorAll('[role="tablist"], [data-tabs]')
        );

        tabLists.forEach(tabList => {
            const tabs = tabList.querySelectorAll('[data-toggle="tab"]');

            if (!tabs.length) return;

            const activeTab = Array.from(tabs).find(
                tab => tab.dataset.state === 'active' ||
                    tab.getAttribute('aria-selected') === 'true'
            );

            if (activeTab) {
                this.activate(activeTab, null, false);
            }
        });
    }

    /**
     * Handle tab clicks.
     */
    handleClick = (e) => {
        const toggle = e.target.closest('[data-toggle="tab"]');

        if (!toggle) return;

        this.activate(toggle, e);
    };

    /**
     * Activate a tab.
     */
    activate(toggle, e = null, syncHash = true) {
        if (e) e.preventDefault();

        const targetSelector = toggle.dataset.target || toggle.getAttribute('href');

        if (!targetSelector || targetSelector === '#') return;

        let targetPane;

        try {
            targetPane = document.querySelector(targetSelector);
        } catch {
            return;
        }

        if (!targetPane) return;

        const tabList = toggle.closest('[role="tablist"], [data-tabs]');
        const paneContainer = targetPane.parentElement;

        // Deactivate sibling tabs.
        if (tabList) {
            tabList.querySelectorAll('[data-toggle="tab"]').forEach(tab => {
                tab.setAttribute('aria-selected', 'false');
                tab.dataset.state = 'inactive';
            });
        }

        // Hide sibling panes.
        if (paneContainer) {
            Array.from(paneContainer.children).forEach(pane => {
                if (pane.hasAttribute('data-tab-pane')) {
                    pane.classList.add('hidden');
                    pane.dataset.state = 'inactive';
                }
            });
        }

        // Activate selected tab.
        toggle.setAttribute('aria-selected', 'true');
        toggle.dataset.state = 'active';

        targetPane.classList.remove('hidden');
        targetPane.dataset.state = 'active';

        // Synchronize URL hash.
        if (
            syncHash &&
            tabList?.dataset.syncHash === 'true' &&
            targetSelector.startsWith('#')
        ) {
            history.replaceState(null, '', targetSelector);
        }

        toggle.dispatchEvent(
            new CustomEvent('spice:tab:shown', {
                bubbles: true,
                detail: {
                    tab: toggle,
                    pane: targetPane
                }
            })
        );
    }

    /**
     * Activate tab matching the current URL hash.
     */
    initFromHash() {
        const hash = window.location.hash;

        if (!hash) return;

        const tabs = document.querySelectorAll('[data-toggle="tab"]');

        const matchingTab = Array.from(tabs).find(tab => {
            return tab.dataset.target === hash ||
                tab.getAttribute('href') === hash;
        });

        if (matchingTab) {
            this.activate(matchingTab, null, false);
        }
    }

    /**
     * Handle browser hash changes.
     */
    handleHashChange = () => {
        this.initFromHash();
    };

    /**
     * Destroy component listeners.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);
        window.removeEventListener('hashchange', this.handleHashChange);
    }
}
