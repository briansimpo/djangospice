
class SpiceToastElement extends HTMLElement {

    connectedCallback() {
        if (this.initialized) return;

        this.initialized = true;

        this.classList.add(
            'fixed',
            'bottom-6',
            'left-6',
            'z-[9999]',
            'pointer-events-none',
            'flex',
            'flex-col',
            'gap-3'
        );

        if (!this.querySelector('template')) {
            this.innerHTML = `
                <template>
                    <div
                        data-toast
                        data-type="info"
                        role="alert"
                        class="
                            pointer-events-auto flex items-center justify-between gap-6
                            min-w-[360px] max-w-md px-5 py-4
                            bg-[#202124] text-white border border-white/10
                            border-l-4 border-l-blue-500
                            rounded-lg shadow-2xl
                            transition-all duration-300
                            translate-y-4 opacity-0">

                        <div class="flex-1 min-w-0">
                            <p
                                data-toast-message
                                class="text-base font-medium leading-relaxed tracking-wide">
                            </p>
                        </div>

                        <button
                            type="button"
                            data-dismiss="toast"
                            class="
                                shrink-0 text-gray-300 hover:text-white
                                transition-colors text-sm font-semibold
                                uppercase px-2 py-1 rounded hover:bg-white/10"
                            aria-label="Dismiss notification">
                            Dismiss
                        </button>
                    </div>
                </template>
            `;
        }
    }
}

if (!customElements.get('spice-toast')) {
    customElements.define('spice-toast', SpiceToastElement);
}
