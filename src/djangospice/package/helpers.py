from djangospice.package.discovery import PackageDiscovery


def djangospice_packages(project_dir, installed_apps, app_directories=["apps"]):

    packages = PackageDiscovery(
        project_dir=project_dir,
        installed_apps=installed_apps,
        app_directories=app_directories,
    ).build()

    return packages