from __future__ import annotations

import functools
import importlib

@functools.lru_cache(maxsize=1024)
def resolve_class(class_path: str) -> type:
    """
    Optimizes dynamic imports by caching resolved Python class paths.
    Prevents repeated disk lookups during heavy recursive deserialization.
    """
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

