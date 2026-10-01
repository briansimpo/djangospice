from __future__ import annotations

import logging

from typing import TypeVar

from django.apps import apps

from .app import AppConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AppDiscovery:
    """
    A utility class responsible for discovering specific app types 
    within the installed Django application configurations.
    """

    def get_apps(self) -> list[AppConfig]:
        """
        Iterates through all installed Django app configs and filters 
        them to find instances of AppConfig.

        Returns:
            list[AppConfig]: A list of discovered AppConfig instances currently registered in the Django project.
        """
        return [
            config for config in apps.get_app_configs() 
            if isinstance(config, AppConfig)
        ]
        
        
