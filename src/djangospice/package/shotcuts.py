from pathlib import Path
from typing import Iterable

from djangospice.package.discovery import PackageDiscovery


def djangospice_packages(project_dir: str | Path, app_directories: Iterable[str] = ("apps",)) -> list[str]:
    """
    Discover Djangospice built-in and project applications.

    Returns additional INSTALLED_APPS entries.
    """

    discovery = PackageDiscovery(
        project_dir=project_dir,
        app_directories=app_directories,
    )

    return discovery.build()