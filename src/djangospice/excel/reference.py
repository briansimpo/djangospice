from typing import Dict, List, Any, Tuple
from django.db.models import Field, Model
from tablib import Dataset
from .inspection import ModelInspector


class ReferenceField:
    """Utility class to extract relationship fields from Django models."""
    @staticmethod
    def get_foreign_fields(model: Model, fields: List[str], custom_qs: Dict) -> List[Field]:
        model_fks = {f.name: f for f in model._meta.get_fields() 
                     if f.is_relation and f.many_to_one and f.name in fields}
        result = []
        for name in fields:
            if name in model_fks:
                field = model_fks[name]
                if name in custom_qs:
                    field._custom_queryset = custom_qs[name]
                result.append(field)
        return result

    @staticmethod
    def get_choice_fields(model: Model, fields: List[str], custom_choices: Dict) -> List[Field]:
        model_choices = {f.name: f for f in model._meta.get_fields() 
                         if not f.is_relation and f.choices and f.name in fields}
        for name, choices in custom_choices.items():
            if name in model_choices:
                model_choices[name].choices = choices
        return list(model_choices.values())


class ReferenceMapBuilder:
    """
    Builder class to construct the relational reference map 
    for Excel data validation and dropdowns.
    """
    
    def __init__(self, model: Any, fields: Any, custom_foreign: Dict[str, Any], custom_choices: Dict[str, Any]):
        self.model = model
        self.fields = fields
        self.custom_foreign = custom_foreign
        self.custom_choices = custom_choices
        self._refs: Dict[str, Tuple[str, Dataset]] = {}

    def add_foreign_keys(self) -> 'ReferenceMapBuilder':
        """Processes and adds foreign key relationships to the reference map."""
        fks = ReferenceField.get_foreign_fields(self.model, self.fields, self.custom_foreign)
        
        for field in fks:
            queryset = getattr(field, "_custom_queryset", field.remote_field.model.objects.all())
            sheet_name = ModelInspector.get_sheet_name(field.remote_field.model)
            dataset = ModelInspector.get_relation_dataset(queryset)
            
            self._refs[field.name.lower()] = (sheet_name, dataset)
            
        return self

    def add_choices(self) -> 'ReferenceMapBuilder':
        """Processes and adds static choice fields to the reference map."""
        chs = ReferenceField.get_choice_fields(self.model, self.fields, self.custom_choices)
        
        for field in chs:
            # Excel sheet names have a hard limit of 31 characters
            sheet_name = field.name[:31] 
            dataset = ModelInspector.get_relation_dataset(field.choices)
            
            self._refs[field.name.lower()] = (sheet_name, dataset)
            
        return self

    def build(self) -> Dict[str, Tuple[str, Dataset]]:
        """Returns the fully constructed reference map."""
        return self._refs