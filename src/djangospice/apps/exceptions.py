class AppRegistryError(Exception):
    """Base exception for app registry operations."""


class AppNotRegistered(AppRegistryError):
    pass


class AppAlreadyRegistered(AppRegistryError):
    pass


class AppDependencyError(AppRegistryError):
    pass


class AppStateError(AppRegistryError):
    pass
