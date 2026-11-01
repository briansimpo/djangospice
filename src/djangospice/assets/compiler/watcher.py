"""Development watcher and WebSocket HMR broadcaster."""
import asyncio
import json
import logging
import time
from pathlib import PurePosixPath
from urllib.parse import urljoin

from django.conf import settings

from djangospice.assets.compiler.builder import build
from djangospice.assets.conf import get_setting
from djangospice.assets.discovery.apps import watch_roots
from djangospice.assets.exceptions import AssetBuildError

logger = logging.getLogger(__name__)


async def run_watcher():
    try:
        from watchfiles import awatch
        from websockets.asyncio.server import serve
    except ImportError as exc:
        raise RuntimeError(
            "Watch mode requires development dependencies. Install with "
            '`pip install "djangospice-assets[dev]"`.'
        ) from exc

    roots = watch_roots()
    if not roots:
        raise RuntimeError("No Djangospice static asset directories were discovered to watch.")

    clients = set()

    async def handler(websocket):
        clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            clients.discard(websocket)

    async def broadcast(message):
        if not clients:
            return
        payload = json.dumps(message)
        await asyncio.gather(*(client.send(payload) for client in tuple(clients)), return_exceptions=True)

    try:
        result = await asyncio.to_thread(build, development=True)
    except AssetBuildError as exc:
        logger.error("Initial asset build failed: %s", exc)
        raise

    logger.info("Initial build complete: JS=%s CSS=%s", result["js"], result["css"])
    host, port = get_setting("HMR_BIND_HOST"), int(get_setting("HMR_PORT"))
    debounce = max(50, int(get_setting("WATCH_DEBOUNCE")))

    async with serve(handler, host, port):
        logger.info("Djangospice HMR listening on ws://%s:%s%s", host, port, get_setting("HMR_PATH"))
        logger.info("Watching: %s", ", ".join(roots))
        async for changes in awatch(*roots, debounce=debounce, step=100):
            changed_paths = [str(change[1]) for change in changes]
            css_changed = any(path.lower().endswith((".css",)) for path in changed_paths)
            js_changed = any(path.lower().endswith((".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")) for path in changed_paths)
            if not (css_changed or js_changed):
                continue
            try:
                result = await asyncio.to_thread(build, development=True)
            except AssetBuildError:
                logger.exception("Asset rebuild failed; keeping last successful bundle.")
                continue
            version = str(time.time_ns())
            logger.info("Assets rebuilt: JS=%s CSS=%s", result["js"], result["css"])
            if js_changed:
                await broadcast({"type": "js", "version": version})
            elif css_changed:
                if result["css"]:
                    prefix = str(settings.STATIC_URL)
                    if not prefix.endswith("/"):
                        prefix += "/"
                    relative = PurePosixPath(get_setting("OUTPUT_DIR")) / result["css"]
                    css_url = urljoin(prefix, str(relative))
                    await broadcast({"type": "css", "version": version, "url": css_url})
                else:
                    await broadcast({"type": "reload", "version": version})
