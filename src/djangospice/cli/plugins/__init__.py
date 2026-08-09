from djangospice.container import container
from .installer import PluginInstaller
from .loader import PluginLoader


plugin_loader = PluginLoader(container)
plugin_installer = PluginInstaller(plugin_loader) 
