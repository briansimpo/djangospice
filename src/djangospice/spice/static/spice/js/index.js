
import "./html/index.js";

import { SpiceUI } from './ui.js';
import { SpiceSocket } from './socket.js';
import { SpiceRouter } from './router.js';
import { SpiceTable } from './table.js';
import { initializeLookup, destroyLookup } from './lookup.js';

import { initialize as initializeNotification } from "./notification.js";
import { initialize as initializeJob } from "./job.js";


/* -------------------------------------------------------------------------- */
/* Environment                                                                */
/* -------------------------------------------------------------------------- */

const isBrowser =
    typeof window !== 'undefined' &&
    typeof document !== 'undefined';


/* -------------------------------------------------------------------------- */
/* Application Services                                                       */
/* -------------------------------------------------------------------------- */

export const socket = isBrowser ? new SpiceSocket() : null;
export const router = isBrowser ? new SpiceRouter() : null;
export const ui = isBrowser ? new SpiceUI() : null;


/* -------------------------------------------------------------------------- */
/* Global Namespace                                                           */
/* -------------------------------------------------------------------------- */

if (isBrowser) {
    window.SpiceUI = SpiceUI;
    window.SpiceSocket = SpiceSocket;
    window.SpiceRouter = SpiceRouter;
    window.SpiceTable = SpiceTable;

    window.spice ??= {};

    Object.assign(window.spice, {
        ui,
        socket,
        router,
    });
}


/* -------------------------------------------------------------------------- */
/* Lifecycle State                                                            */
/* -------------------------------------------------------------------------- */

let initialized = false;

const tableInstances = new WeakMap();


/* -------------------------------------------------------------------------- */
/* DOM Utilities                                                              */
/* -------------------------------------------------------------------------- */

function onReady(callback) {
    if (!isBrowser) return;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', callback, {
            once: true,
        });
    } else {
        callback();
    }
}

function getElements(root, selector) {
    if (!root) return [];

    const elements = [];

    if (root.matches?.(selector)) {
        elements.push(root);
    }

    elements.push(...(root.querySelectorAll?.(selector) || []));

    return elements;
}


/* -------------------------------------------------------------------------- */
/* Table Lifecycle                                                            */
/* -------------------------------------------------------------------------- */

function initTables(root) {
    getElements(root, '[data-table]').forEach(element => {
        if (tableInstances.has(element)) return;

        const instance = new SpiceTable(element);

        tableInstances.set(element, instance);
    });
}

function destroyTables(root) {
    getElements(root, '[data-table]').forEach(element => {
        const instance = tableInstances.get(element);

        if (!instance) return;

        instance.destroy?.();
        tableInstances.delete(element);
    });
}


/* -------------------------------------------------------------------------- */
/* Lookup Lifecycle                                                           */
/* -------------------------------------------------------------------------- */

function initLookups(root) {
    if (!root) return;

    initializeLookup(root);
}

function destroyLookups(root) {
    if (!root) return;

    destroyLookup(root);
}

/* -------------------------------------------------------------------------- */
/* Application Initialization                                                */
/* -------------------------------------------------------------------------- */

export function init(root = document) {
    if (!isBrowser || !root) return;

    // Start application-wide services once.
    if (!initialized) {
        initialized = true;

        router.start();
        router.processDocument();
    }

    // Initialize DOM-dependent components.
    initTables(root);
    initLookups(root);

    // Initialize Djangospice UI components.
    ui.initStates(root);
    initializeNotification(socket)
    initializeJob(socket)
}


/* -------------------------------------------------------------------------- */
/* HTMX Lifecycle                                                             */
/* -------------------------------------------------------------------------- */

function handleHTMXLoad(event) {
    init(event.detail?.elt || document);
}

function handleHTMXCleanup(event) {
    const root = event.detail?.elt;

    if (!root) return;

    destroyTables(root);
    destroyLookups(root);
}


/* -------------------------------------------------------------------------- */
/* Runtime Cleanup                                                            */
/* -------------------------------------------------------------------------- */

export function destroy() {
    if (!isBrowser) return;

    document.removeEventListener('htmx:load', handleHTMXLoad);
    document.removeEventListener(
        'htmx:beforeCleanupElement',
        handleHTMXCleanup
    );

    destroyTables(document);
    destroyLookups(document);

    ui?.destroy?.();
    socket?.destroy?.();

    initialized = false;
}


/* -------------------------------------------------------------------------- */
/* Bootstrap                                                                  */
/* -------------------------------------------------------------------------- */

if (isBrowser) {
    document.addEventListener('htmx:load', handleHTMXLoad);

    document.addEventListener(
        'htmx:beforeCleanupElement',
        handleHTMXCleanup
    );

    onReady(() => init());
}

document.body.addEventListener('htmx:beforeRequest', function (event) {
    if (event.detail.elt.matches('[data-table-export]')) {
        document.getElementById('table-export-loading')?.classList.remove('hidden');
        document.getElementById('table-export-loading')?.classList.add('flex');
    }
});

document.body.addEventListener('htmx:afterRequest', function (event) {
    if (event.detail.elt.matches('[data-table-export]')) {
        document.getElementById('table-export-loading')?.classList.add('hidden');
        document.getElementById('table-export-loading')?.classList.remove('flex');
    }
});