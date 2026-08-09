from typing import List, Dict, Optional, Any


class AppRegistry:
    """
    A centralized registry for managing and looking up applications.
    
    Optimized to provide O(1) lookups for applications by their instance, 
    label, or name using internal hash maps.
    """

    def __init__(self) -> None:
        """Initializes the registry with empty storage structures."""
        self._apps: List[Any] = []
        self._apps_set: set[Any] = set()
        self._apps_by_label: Dict[str, Any] = {}
        self._apps_by_name: Dict[str, Any] = {}

    def register(self, app: Any) -> None:
        """
        Registers an application if it hasn't been registered already.

        Args:
            app (Any): The application instance to register. Ideally features 
                       'label' and 'name' attributes.
        """
        if app in self._apps_set:
            return

        self._apps.append(app)
        self._apps_set.add(app)

        # Safely extract and map attributes if they exist
        label = getattr(app, "label", None)
        name = getattr(app, "name", None)

        if label:
            self._apps_by_label[label] = app
        if name:
            self._apps_by_name[name] = app

    def get_apps(self) -> List[Any]:
        """
        Retrieves all registered applications in registration order.

        Returns:
            List[Any]: A list of all registered application instances.
        """
        return self._apps

    def get_labels(self) -> List[str]:
        """
        Retrieves the labels of all registered applications.

        Returns:
            List[str]: A list of registered application labels.
        """
        return list(self._apps_by_label.keys())

    def get_by_label(self, label: str) -> Optional[Any]:
        """
        Finds a registered application by its unique label.

        Args:
            label (str): The label to search for.

        Returns:
            Optional[Any]: The matched application instance, or None if not found.
        """
        return self._apps_by_label.get(label)

    def get_by_name(self, name: str) -> Optional[Any]:
        """
        Finds a registered application by its unique name.

        Args:
            name (str): The name to search for.

        Returns:
            Optional[Any]: The matched application instance, or None if not found.
        """
        return self._apps_by_name.get(name)

    def has_app(self, app: Any) -> bool:
        """
        Checks if a specific application instance is already registered.

        Args:
            app (Any): The application instance to verify.

        Returns:
            bool: True if registered, False otherwise.
        """
        return app in self._apps_set

    def has_label(self, label: str) -> bool:
        """
        Checks if an application with the given label exists in the registry.

        Args:
            label (str): The label to verify.

        Returns:
            bool: True if the label exists, False otherwise.
        """
        return label in self._apps_by_label


# Global registry instance
registry = AppRegistry()