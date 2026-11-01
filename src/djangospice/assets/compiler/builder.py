
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from djangospice.assets.compiler.entrypoint import write_entrypoint
from djangospice.assets.compiler.esbuild import run_esbuild
from djangospice.assets.conf import get_build_root, get_setting
from djangospice.assets.discovery.apps import discover_entrypoints
from djangospice.assets.exceptions import AssetBuildError


def _sha256(path):
    digest = hashlib.sha256()

    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()



def _compile(
    sources,
    temp_dir,
    *,
    name,
    kind,
    minify,
    sourcemap,
):
    """Compile JavaScript or CSS entry points."""

    temp_dir = Path(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    entrypoint = write_entrypoint(
        sources,
        temp_dir / f"{name}-entry.js",
        kind=kind,
    )

    output = temp_dir / f"{name}.js"

    run_esbuild(
        entrypoint,
        output,
        kind=kind,
        minify=minify,
        sourcemap=sourcemap,
    )

    expected_output = (
        output if kind == "js"
        else output.with_suffix(".css")
    )

    if not expected_output.exists():
        raise AssetBuildError(
            f"esbuild did not produce expected {kind.upper()} output: "
            f"{expected_output}"
        )

    return expected_output


def _publish(source, output_dir, prefix, extension):
    """Publish an output using its content hash."""

    digest = _sha256(source)[:12]

    filename = f"{prefix}.{digest}.{extension}"
    destination = output_dir / filename

    shutil.copy2(source, destination)

    return filename


def _publish_sourcemap(source, output_dir, filename, extension):
    """Publish a source map alongside its corresponding asset."""

    if not source.exists():
        return None

    map_filename = f"{Path(filename).stem}.{extension}.map"

    shutil.copy2(
        source,
        output_dir / map_filename,
    )

    return map_filename


def build(*, development=False, production=False):
    """Build unified JavaScript and CSS assets."""

    if development and production:
        raise AssetBuildError(
            "Development and production modes are mutually exclusive."
        )

    js_sources = discover_entrypoints(asset_type="js")
    css_sources = discover_entrypoints(asset_type="css")

    if not js_sources and not css_sources:
        raise AssetBuildError(
            "No Djangospice JavaScript or CSS entry points found."
        )

    build_root = get_build_root()

    output_dir = build_root / get_setting("OUTPUT_DIR")
    output_dir.mkdir(parents=True, exist_ok=True)

    minify = production or (
        not development and bool(get_setting("MINIFY"))
    )

    sourcemap = development or (
        not production and bool(get_setting("SOURCEMAP"))
    )

    js_filename = None
    css_filename = None

    with tempfile.TemporaryDirectory(
        prefix="djangospice-assets-"
    ) as temporary_directory:

        temporary_directory = Path(temporary_directory)

        js_temp = temporary_directory / "javascript"
        css_temp = temporary_directory / "stylesheets"

        js_output = None
        css_output = None

        # Compile JavaScript.
        if js_sources:
            js_output = _compile(
                js_sources,
                js_temp,
                name="javascript",
                kind="js",
                minify=minify,
                sourcemap=sourcemap,
            )
            

        # Compile CSS.
        if css_sources:
            css_output = _compile(
                css_sources,
                css_temp,
                name="stylesheet",
                kind="css",
                minify=minify,
                sourcemap=sourcemap,
            )

        # Publish assets only after both compilations succeed.
        if js_output:
            js_filename = _publish(
                js_output,
                output_dir,
                "djangospice",
                "js",
            )

            if sourcemap:
                _publish_sourcemap(
                    Path(str(js_output) + ".map"),
                    output_dir,
                    js_filename,
                    "js",
                )

        if css_output:
            css_filename = _publish(
                css_output,
                output_dir,
                "djangospice",
                "css",
            )

            if sourcemap:
                _publish_sourcemap(
                    Path(str(css_output) + ".map"),
                    output_dir,
                    css_filename,
                    "css",
                )

    # Update manifest after successful compilation.
    manifest_path = output_dir / "manifest.json"

    manifest = {
        "version": 1,
        "js": {
            "main": js_filename,
        },
        "css": {
            "main": css_filename,
        },
        "apps": sorted(
            {
                label
                for label, _ in js_sources + css_sources
            }
        ),
        "source_count": {
            "js": len(js_sources),
            "css": len(css_sources),
        },
    }

    temporary_manifest = manifest_path.with_suffix(".json.tmp")

    temporary_manifest.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    temporary_manifest.replace(manifest_path)

    return {
        "js": js_filename,
        "css": css_filename,
        "manifest": str(manifest_path),
        "apps": manifest["apps"],
        "source_count": manifest["source_count"],
        "minified": minify,
        "sourcemap": sourcemap,
    }


def clean():
    """Remove generated Djangospice bundles and manifest."""

    output_dir = (
        get_build_root() / get_setting("OUTPUT_DIR")
    )

    if not output_dir.exists():
        return 0

    removed = 0

    for path in output_dir.iterdir():
        if not path.is_file():
            continue

        if (
            path.name.startswith("djangospice.")
            or path.name == "manifest.json"
        ):
            path.unlink()
            removed += 1

    return removed
