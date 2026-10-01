import os

from django.apps import apps
from django.templatetags.static import static

from djangospice.urls import get_valid_url
from djangospice.config.app import AppConfig
from djangospice.config.loader import Options, Settings, Permissions, Fixtures, PeriodicTasks

      
class AppInstaller:
    """
    Main class to handle the installation and configuration of an application within a Django project.
    """
    default_icon = "img/app.png"

    def __init__(self, app_config: AppConfig, ignore_errors: bool = True) -> None:
        """
        Initialize the AppInstaller instance.

        Args:
            app_config (AppConfig): The Django application configuration object.
            ignore_errors (bool, optional): Whether to ignore errors during installation. Defaults to True.
        """
        self.app_config = app_config
        self.ignore_errors = ignore_errors

        self.app_path = app_config.path
        self.app_name = app_config.name
        self.app_label = app_config.label
        self.verbose_name = app_config.verbose_name        

        self.description = getattr(app_config, "description", self.verbose_name)
        self.is_default = getattr(app_config, "is_default", True)
        self.is_service = getattr(app_config, "is_service", False)
        self.icon = self._get_icon_url(getattr(app_config, "icon", None))
        self.url = self._get_valid_url(getattr(app_config, "url", None))

        self.options_loader = Options(app_config, ignore_errors=ignore_errors)
        self.settings_loader = Settings(app_config)
        self.permissions_loader = Permissions(app_config, ignore_errors=ignore_errors)
        self.fixtures_loader = Fixtures(app_config, ignore_errors=ignore_errors)
        self.tasks_loader = PeriodicTasks(app_config, ignore_errors=ignore_errors)


    def _get_icon_url(self, icon: str) -> str:
        """
        Get the URL of the app"s icon, falling back to a default if necessary.

        Args:
            icon (str): The icon filename.

        Returns:
            str: URL to the icon.
        """
        file_path = os.path.join(self.app_label, icon) if icon else self.default_icon
        return static(file_path)
    
    def _get_valid_url(self, url: str) -> str:
        """
        Validate and return a properly formatted URL.

        Args:
            url (str): The URL string.

        Returns:
            str: Validated URL or None if the URL is invalid.
        """
        return get_valid_url(url) if url else None
    
    def _get_app_model(self):
        """
        Get the App model from the app.

        Returns:
            Model: The App model.
        """
        from .models import namespace
        return apps.get_model(namespace, "App")

    def create_app(self):
        """
        Create or get the app instance in the database.

        Returns:
            tuple: The app instance and a boolean indicating if it was created.
        """
        try:
            model = self._get_app_model()

            app, created = model.objects.get_or_create(
                name=self.app_name,
                verbose_name=self.verbose_name,
                label=self.app_label,
                is_default=self.is_default,
                is_service=self.is_service,
                url=self.url,
                icon=self.icon
            )
            return app, created
        except Exception as e:
            pass
    
    def load_permissions(self):
        """
        Load app permissions from the default JSON file.
        """
        try:
            self.permissions_loader.load()
        except Exception as e:
            pass

    def load_options(self):
        """
        Load app options from the default JSON file.
        """
        try:
            self.options_loader.load()
        except Exception as e:
            pass

    def load_settings(self):
        """
        Load app settings from the default JSON file.
        """
        try:
           self.settings_loader.load()
        except Exception as e:
            pass
        
    def load_fixtures(self):
        try:
           self.fixtures_loader.load()
        except Exception as e:
            pass

    def load_tasks(self):
        try:
           self.tasks_loader.load()
        except Exception as e:
            pass

    def install(self):
        """
        Install the app by creating the instance, loading options, and permissions.
        """
        try:
            self.create_app()
            self.load_options()
            self.load_permissions()
            self.load_fixtures()
            self.load_settings()
            self.load_tasks()
        except Exception as e:
            pass
