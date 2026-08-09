from importlib import import_module
from djangospice.apps import registry

def discover_routers():

    for app in registry.get_apps():

        try:
            import_module(f"{app.name}.api.router")
        except ModuleNotFoundError as exc:
            expected = (f"{app.name}.api.router")
            if exc.name == expected:
                continue
            raise
        
