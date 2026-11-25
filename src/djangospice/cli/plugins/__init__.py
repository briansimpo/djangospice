from djangospice.services.registry import service_registry
from .installer import PluginInstaller
from .loader import PluginLoader


plugin_loader = PluginLoader(service_registry)
plugin_installer = PluginInstaller(plugin_loader) 


__all__ = [
    "plugin_loader",
    "plugin_installer",
]
