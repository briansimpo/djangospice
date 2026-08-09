from typing import Dict, List, Any
from import_export.resources import ModelResource
from .config import ResourceConfig


class BaseResource(ModelResource):
    """
    The orchestration layer connecting Django Models to the Excel Engine.
    
    This resource extends django-import-export's ModelResource to provide
    configurable options for data protection, custom export names, and
    field-level visibility.
    """
    class Meta:
        abstract = True
        export_data = False
        protect = True
        hidden_fields: List[str] = []
        foreign_fields: Dict[str, Any] = {}
        choice_fields: Dict[str, Any] = {}

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the BaseResource and its configuration state.

        Args:
            **kwargs: Optional overrides for the model, export settings, and custom fields.
        """
        super().__init__(**kwargs)
        self.model: Any = kwargs.get('model', getattr(self._meta, 'model', None))
        
        # Initialize the dataclass instead of a dictionary
        self.config: ResourceConfig = ResourceConfig(
            export_data=kwargs.get('export_data', getattr(self._meta, 'export_data', False)),
            protect=kwargs.get('protect', getattr(self._meta, 'protect', True)),
            hidden_fields=kwargs.get('hidden_fields', self.get_hidden_fields()),
            export_name=kwargs.get('export_name', getattr(self._meta, 'export_name', None)),
        )
        
        self.custom_foreign: Dict[str, Any] = kwargs.get('foreign_fields', self.get_foreign_fields())
        self.custom_choices: Dict[str, Any] = kwargs.get('choice_fields', self.get_choice_fields())
        
    def get_foreign_fields(self) -> Dict[str, Any]:
        """
        Retrieve foreign key field configurations from the Meta class.

        Returns:
            Dict[str, Any]: Dictionary mapping field names to foreign key configurations.
        """
        return getattr(self._meta, 'foreign_fields', {})
    
    def get_choice_fields(self) -> Dict[str, Any]:
        """
        Retrieve choice field configurations from the Meta class.

        Returns:
            Dict[str, Any]: Dictionary mapping field names to choice configurations.
        """
        return getattr(self._meta, 'choice_fields', {})
    
    def get_hidden_fields(self) -> List[str]:
        """
        Retrieve the list of hidden fields from the Meta class.

        Returns:
            List[str]: List of field names to hide.
        """
        return getattr(self._meta, 'hidden_fields', [])
    
    def allow_data_export(self, allow: bool = True) -> 'BaseResource':
        """
        Enable or disable data exporting on the configuration state.

        Args:
            allow (bool): True to enable export, False to disable. Defaults to True.

        Returns:
            BaseResource: The current instance for method chaining.
        """
        self.config.export_data = allow
        return self

    def set_export_name(self, name: str) -> 'BaseResource':
        """
        Set a custom name for the configuration export state.

        Args:
            name (str): The desired name for the export.

        Returns:
            BaseResource: The current instance for method chaining.
        """
        self.config.export_name = name
        return self
    
    def is_blank(self) -> bool: 
        """
        Check if the underlying Django model currently has no records.

        Returns:
            bool: True if there are no records, False otherwise.
        """
        return not self.model.objects.exists()
    
    def is_filled(self) -> bool: 
        """
        Check if the underlying Django model has existing records.

        Returns:
            bool: True if there are records, False otherwise.
        """
        return self.model.objects.exists()