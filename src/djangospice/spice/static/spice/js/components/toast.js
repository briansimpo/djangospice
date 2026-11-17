
export class Toast {

    /**
     * Initialize toast component.
     */
    init() {
        this.initStates();

        document.addEventListener('click', this.handleClick);
    }

    /**
     * Show a programmatic toast.
     *
     * @param {Object} options
     * @param {string} options.message
     * @param {string} options.type
     * @param {number} options.duration
     */
    show({message = '', type = 'info', duration = 5000} = {}) {
        const container = document.querySelector('spice-toast');
        const template = container?.querySelector('template');

        if (!container || !template) {
            console.warn('Toast container or template is missing.');
            return null;
        }

        const fragment = template.content.cloneNode(true);
        const toast = fragment.querySelector('[data-toast]');

        if (!toast) {
            console.warn('Toast template must contain an element with [data-toast].');
            return null;
        }

        toast.dataset.type = type;

        const messageElement = toast.querySelector('[data-toast-message]');

        if (messageElement) {
            messageElement.textContent = message;
        }

        if (duration !== undefined && duration !== null) {
            toast.dataset.duration = String(duration);
        }

        container.appendChild(fragment);

        this.initToasts(toast);

        return toast;
    }

    /**
     * Initialize toast states.
     */
    initStates(root = document) {
        this.initToasts(root);
    }

    /**
     * Initialize server-rendered and dynamically inserted toasts.
     */
    initToasts(root = document) {
        const toasts = [];

        if (root.matches?.('[data-toast]')) {
            toasts.push(root);
        }

        toasts.push(...root.querySelectorAll('[data-toast]'));

        toasts.forEach(toast => {
            if (toast.dataset.initialized === 'true') return;

            toast.dataset.initialized = 'true';

            requestAnimationFrame(() => {
                toast.classList.remove(
                    'translate-y-2',
                    'translate-y-4',
                    'opacity-0'
                );
            });

            const duration = toast.dataset.duration === undefined
                ? 5000
                : Number.parseInt(toast.dataset.duration, 10);

            if (Number.isFinite(duration) && duration > 0) {
                toast.dataset.timer = setTimeout(() => {
                    this.dismiss(toast);
                }, duration);
            }
        });
    }

    /**
     * Handle toast and alert dismissal.
     */
    handleClick = (e) => {
        const dismiss = e.target.closest(
            '[data-dismiss="toast"], [data-dismiss="alert"]'
        );

        if (!dismiss) return;

        e.preventDefault();

        this.handleDismiss(dismiss);
    };

    /**
     * Dismiss a toast or alert.
     */
    handleDismiss(target) {
        const toast = target.closest('[data-toast]');

        if (toast) {
            this.dismiss(toast);
            return true;
        }

        const alert = target.closest('[data-alert]');

        if (alert) {
            this.dismissAlert(alert);
            return true;
        }

        return false;
    }

    /**
     * Dismiss toast with animation.
     */
    dismiss(toast) {
        if (!toast || toast.dataset.dismissing === 'true') return;

        toast.dataset.dismissing = 'true';

        if (toast.dataset.timer) {
            clearTimeout(Number(toast.dataset.timer));
            delete toast.dataset.timer;
        }

        toast.classList.add('translate-y-2', 'opacity-0');

        setTimeout(() => {
            toast.remove();
        }, 200);
    }

    /**
     * Dismiss alert with animation.
     */
    dismissAlert(alert) {
        if (!alert || alert.dataset.dismissing === 'true') return;

        alert.dataset.dismissing = 'true';

        alert.classList.add(
            'opacity-0',
            'scale-95',
            'transition-all',
            'duration-150'
        );

        setTimeout(() => {
            alert.remove();
        }, 150);
    }

    /**
     * Destroy component listeners and timers.
     */
    destroy() {
        document.removeEventListener('click', this.handleClick);

        document.querySelectorAll('[data-toast]').forEach(toast => {
            if (toast.dataset.timer) {
                clearTimeout(Number(toast.dataset.timer));
                delete toast.dataset.timer;
            }
        });
    }
}
