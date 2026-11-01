import asyncio

from django.core.management.base import BaseCommand, CommandError

from djangospice.assets.compiler.builder import build, clean
from djangospice.assets.compiler.watcher import run_watcher
from djangospice.assets.discovery.apps import discover_assets
from djangospice.assets.exceptions import AssetBuildError


class Command(BaseCommand):
    help = "Discover, build, watch, and manage Djangospice assets."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)
        build_parser = subparsers.add_parser("build", help="Build unified JS and CSS bundles.")
        mode = build_parser.add_mutually_exclusive_group()
        mode.add_argument("--development", action="store_true")
        mode.add_argument("--production", action="store_true")
        subparsers.add_parser("discover", help="List discovered app asset entry points.")
        subparsers.add_parser("clean", help="Remove generated assets.")
        subparsers.add_parser("watch", help="Watch source files and run development HMR.")

    def handle(self, *args, **options):
        action = options["action"]
        if action == "discover":
            entries = discover_assets()
            for item in entries:
                self.stdout.write(f"{item['app']}: JS={item['js'] or '-'} CSS={item['css'] or '-'}")
            self.stdout.write(self.style.SUCCESS(f"Discovered {len(entries)} app(s)."))
            return
        if action == "clean":
            self.stdout.write(self.style.SUCCESS(f"Removed {clean()} generated file(s)."))
            return
        if action == "watch":
            try:
                asyncio.run(run_watcher())
            except KeyboardInterrupt:
                self.stdout.write("\\nStopped Djangospice asset watcher.")
            except Exception as exc:
                raise CommandError(str(exc)) from exc
            return
        try:
            result = build(development=options["development"], production=options["production"])
        except AssetBuildError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Djangospice assets built successfully."))
        self.stdout.write(f"JavaScript: {result['js'] or 'none'}")
        self.stdout.write(f"CSS: {result['css'] or 'none'}")
        self.stdout.write(f"Apps: {', '.join(result['apps'])}")
        self.stdout.write(f"Manifest: {result['manifest']}")
