
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def get_asgi_application():
    """
    Resolve the project's ASGI application.

    Priority:
    1. ASGI_APPLICATION setting.
    2. Infer the ASGI module from DJANGO_SETTINGS_MODULE.
    """
    application = getattr(settings, "ASGI_APPLICATION", None)

    if application:
        if ":" in application:
            return application

        module, attribute = application.rsplit(".", 1)
        return f"{module}:{attribute}"

    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")

    if not settings_module:
        raise CommandError(
            "Cannot determine ASGI application. "
            "Set ASGI_APPLICATION in your Django settings."
        )

    parts = settings_module.split(".")

    if "settings" in parts:
        project_module = ".".join(parts[:parts.index("settings")])
    elif len(parts) > 1:
        project_module = ".".join(parts[:-1])
    else:
        project_module = parts[0]

    return f"{project_module}.asgi:application"


class Command(BaseCommand):
    help = "Run the Djangospice ASGI server."

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host address (default: 127.0.0.1).",
        )

        parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port number (default: 8000).",
        )

        parser.add_argument(
            "--workers",
            type=int,
            default=1,
            help="Number of worker processes.",
        )

        parser.add_argument(
            "--reload",
            action="store_true",
            help="Enable automatic reloading (development only).",
        )

        parser.add_argument(
            "--log-level",
            default="info",
            choices=["critical", "error", "warning", "info", "debug", "trace"],
            help="Logging level.",
        )

        parser.add_argument(
            "--access-log",
            action="store_true",
            help="Enable HTTP access logging.",
        )

        parser.add_argument(
            "--proxy-headers",
            action="store_true",
            help="Trust proxy headers from the configured proxy addresses.",
        )

        parser.add_argument(
            "--forwarded-allow-ips",
            default="127.0.0.1",
            help="Trusted proxy IP addresses.",
        )

    def handle(self, *args, **options):
        try:
            import uvicorn
        except ImportError as exc:
            raise CommandError(
                'Uvicorn is required. Install it with: pip install "uvicorn[standard]"'
            ) from exc

        if options["workers"] < 1:
            raise CommandError("--workers must be at least 1.")

        if options["reload"] and options["workers"] > 1:
            raise CommandError(
                "--reload cannot be used with multiple workers."
            )

        application = get_asgi_application()

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting ASGI server at "
                f"http://{options['host']}:{options['port']}"
            )
        )

        uvicorn.run(
            application,
            host=options["host"],
            port=options["port"],
            workers=options["workers"],
            reload=options["reload"],
            log_level=options["log_level"],
            access_log=options["access_log"],
            proxy_headers=options["proxy_headers"],
            forwarded_allow_ips=options["forwarded_allow_ips"],
        )
