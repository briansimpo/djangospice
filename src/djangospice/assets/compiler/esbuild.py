import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings

from djangospice.assets.conf import get_setting
from djangospice.assets.exceptions import AssetBuildError


def resolve_esbuild():
    configured = str(get_setting("ESBUILD_BINARY"))
    candidate = shutil.which(configured)
    if candidate:
        return candidate
    base = Path(settings.BASE_DIR)
    names = ("esbuild.cmd", "esbuild.exe", "esbuild") if os.name == "nt" else ("esbuild",)
    for name in names:
        local = base / "node_modules" / ".bin" / name
        if local.is_file():
            return str(local)
    raise AssetBuildError(
        "Could not find esbuild. Install it with `npm install --save-dev esbuild` "
        "or configure DJANGOSPICE_ASSETS['ESBUILD_BINARY']."
    )


def run_esbuild(entrypoint, output_file, *, kind="js", minify=False, sourcemap=False):
    args = [resolve_esbuild(), str(entrypoint), "--bundle", f"--outfile={output_file}",
            f"--target={get_setting('TARGET')}", "--log-level=warning"]
    if kind == "js":
        args += [f"--format={get_setting('FORMAT')}", f"--platform={get_setting('PLATFORM')}"]
        global_name = get_setting("GLOBAL_NAME")
        if global_name and get_setting("FORMAT") == "iife":
            args.append(f"--global-name={global_name}")
    else:
        args += ["--asset-names=assets/[name]-[hash]"]
    if minify:
        args.append("--minify")
    if sourcemap:
        args.append("--sourcemap")
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise AssetBuildError(f"Unable to execute esbuild: {exc}") from exc
    if result.returncode:
        raise AssetBuildError(f"esbuild failed:\n{(result.stderr or result.stdout).strip()}")
    return result
