from __future__ import annotations

from argparse import ArgumentParser

from django.core.management.base import BaseCommand, CommandError

from djangospice.app_registry.registry import registry
from djangospice.app_registry.services import sync_apps


class Command(BaseCommand):
    """Inspect and synchronize the Djangospice application registry."""

    help = "Inspect and synchronize the Djangospice application registry."

    def add_arguments(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            dest="subcommand",
            metavar="{list,show,sync,enable,disable,dependencies,dependents}",
        )

        subparsers.add_parser(
            "list",
            help="List registered applications.",
        )

        show_parser = subparsers.add_parser(
            "show",
            help="Show application details.",
        )
        show_parser.add_argument("key", help="Application key.")

        subparsers.add_parser(
            "sync",
            help="Discover Django apps and synchronize metadata.",
        )

        for action in ("enable", "disable", "dependencies", "dependents"):
            action_parser = subparsers.add_parser(
                action,
                help=f"{action.capitalize()} application information.",
            )
            action_parser.add_argument("key", help="Application key.")

    def handle(self, *args, **options):
        command = options.get("subcommand") or "list"

        handlers = {
            "list": self.list_apps,
            "show": self.show_app,
            "sync": self.sync,
            "enable": self.enable,
            "disable": self.disable,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
        }

        handler = handlers.get(command)
        if handler is None:
            raise CommandError(f"Unknown subcommand: {command}")

        return handler(options)

    def list_apps(self, options: dict) -> None:
        applications = registry.all().order_by("key")

        if not applications.exists():
            self.stdout.write("No registered applications.")
            return

        headers = (
            f"{'KEY':<35} {'VERSION':<15} "
            f"{'STATUS':<15} {'ENABLED'}"
        )
        self.stdout.write(headers)
        self.stdout.write("-" * len(headers))

        for app in applications:
            self.stdout.write(
                f"{app.key:<35} "
                f"{app.version:<15} "
                f"{app.status:<15} "
                f"{app.enabled}"
            )

    def show_app(self, options: dict) -> None:
        app = self._get_app(options["key"])

        fields = (
            ("Key", app.key),
            ("Name", app.name),
            ("Package", app.package),
            ("Version", app.version),
            ("App label", app.app_label),
            ("Django app", app.django_app),
            ("Status", app.status),
            ("Enabled", app.enabled),
            ("Description", app.description),
            ("Author", app.author),
            ("Homepage", app.homepage),
            ("URL", app.url),
        )

        for label, value in fields:
            self.stdout.write(f"{label + ':':<16} {value or '-'}")

        dependencies = registry.dependencies(app.key)

        if dependencies.exists():
            self.stdout.write("\nDependencies:")
            for dependency in dependencies:
                self._write_dependency(dependency)

        capabilities = app.capabilities.order_by("key")

        if capabilities.exists():
            self.stdout.write("\nCapabilities:")
            for capability in capabilities:
                self.stdout.write(f"  - {capability.key}")

    def sync(self, options: dict) -> None:
        applications = sync_apps()

        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronized {len(applications)} application(s)."
            )
        )

    def enable(self, options: dict) -> None:
        app = self._run_registry_action(
            registry.enable,
            options["key"],
        )
        self.stdout.write(
            self.style.SUCCESS(f"Enabled '{app.key}'.")
        )

    def disable(self, options: dict) -> None:
        app = self._run_registry_action(
            registry.disable,
            options["key"],
        )
        self.stdout.write(
            self.style.SUCCESS(f"Disabled '{app.key}'.")
        )

    def dependencies(self, options: dict) -> None:
        dependencies = registry.dependencies(options["key"])

        if not dependencies.exists():
            self.stdout.write("No dependencies.")
            return

        for dependency in dependencies:
            self._write_dependency(dependency)

    def dependents(self, options: dict) -> None:
        dependents = registry.dependents(options["key"])

        if not dependents.exists():
            self.stdout.write("No dependent applications.")
            return

        for dependency in dependents:
            self.stdout.write(dependency.app.key)

    def _write_dependency(self, dependency) -> None:
        specifier = dependency.version_specifier or "*"
        optional = " (optional)" if dependency.optional else ""

        self.stdout.write(
            f"  - {dependency.dependency_key} "
            f"{specifier}{optional}"
        )

    def _get_app(self, key: str):
        try:
            return registry.get(key)
        except Exception as exc:
            # Preserve unexpected exceptions rather than masking programming
            # errors; only translate the registry's expected lookup error.
            from djangospice.app_registry.exceptions import AppNotRegistered

            if isinstance(exc, AppNotRegistered):
                raise CommandError(str(exc)) from exc
            raise

    def _run_registry_action(self, action, key: str):
        try:
            return action(key)
        except Exception as exc:
            from djangospice.app_registry.exceptions import (
                AppNotRegistered,
                AppStateError,
            )

            if isinstance(exc, (AppNotRegistered, AppStateError)):
                raise CommandError(str(exc)) from exc
            raise