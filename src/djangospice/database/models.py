from __future__ import annotations

import os
import re
import json
import uuid
import semver
from slugify import slugify
from typing import Any

from decimal import Decimal
from datetime import datetime, date, time
from model_utils.models import TimeStampedModel, UUIDModel
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise
from django.db import connection, models
from django.core.exceptions import ValidationError
from .managers import SequenceManager
from .mixins import SerializesModels



class ModelJSONEncoder(DjangoJSONEncoder):
    """
    Standard JSON encoder fallback to ensure custom types safely encode to JSON.
    """
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Promise):
            return str(obj)
        if hasattr(obj, "url"):
            try:
                return obj.url if obj else None
            except ValueError:
                return None
        return super().default(obj)
    

class DirtyFields(models.Model):
    """
    A mixin to track changes (dirty fields) in a Django model and retrieve
    both old and new values for updated fields.
    """
    _original_state = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store_original_state()

    def _store_original_state(self):
        """
        Stores the current state of the instance when it"s loaded or saved.
        """
        if self.pk:  # Only for saved instances
            self._original_state = self._get_current_state_from_db()

    def _get_current_state_from_db(self):
        """
        Retrieves the current state of the instance from the database.
        """
        return self.__class__.objects.filter(pk=self.pk).values(*[field.name for field in self._meta.fields]).first()

    # ------------------ Dirty Field Tracking ------------------

    def get_dirty_fields(self):
        """
        Returns a dictionary of fields that have changed, with their old and new values.
        """
        if not self._original_state:
            return {}

        dirty_fields = {}
        for field in self._meta.fields:
            if self._is_field_dirty(field):
                field_name = field.name
                dirty_fields[field_name] = {
                    "old": self._original_state.get(field_name),
                    "new": getattr(self, field_name),
                }
        return dirty_fields
    
    def get_old_value(self, field_name):
        """
        Returns the old value of a specific field if it"s dirty.
        """
        dirty_fields = self.get_dirty_fields()
        return dirty_fields.get(field_name, {}).get("old")

    def get_new_value(self, field_name):
        """
        Returns the new value of a specific field if it"s dirty.
        """
        dirty_fields = self.get_dirty_fields()
        return dirty_fields.get(field_name, {}).get("new")

    def _is_field_dirty(self, field):
        """
        Checks if a given field has been updated compared to the original state.
        """
        current_value = getattr(self, field.name)
        original_value = self._original_state.get(field.name) if self._original_state else None
        return current_value != original_value

    def is_dirty(self, field_name):
        """
        Checks if a specific field is dirty (updated).
        """
        return field_name in self.get_dirty_fields()

    def save(self, *args, **kwargs):
        """
        Saves the instance and updates the original state after saving.
        """
        super().save(*args, **kwargs)
        self._store_original_state()


class FileFields(models.Model):
    """
    A mixin that provides file deletion capabilities for image and file fields.
    """
    class Meta:
        abstract = True

    def _delete_file(self, file_field):
        """Delete the file associated with the given file field if it exists."""
        if file_field and os.path.isfile(file_field.path):
            try:
                os.remove(file_field.path)
            except:
                pass

    def _handle_file(self, old_instance):
        """Handle deletion of old files if they are updated or cleared."""
        for field in self._get_file_fields():
            old_file = getattr(old_instance, field)
            new_file = getattr(self, field)

            # Delete the old file if it"s being updated or cleared
            if old_file and (old_file != new_file or new_file is None):
                self._delete_file(old_file)

    def _get_file_fields(self):
        """Return a list of image and file fields in the model."""
        return [
            field.name for field in self._meta.fields 
            if isinstance(field, (models.ImageField, models.FileField))
        ]
    
    def save(self, *args, **kwargs):
        # If updating an existing profile, handle file deletions
        if self.pk:
            old_instance = self.__class__.objects.filter(pk=self.pk).first()
            if old_instance:
                self._handle_file(old_instance)

        # Proceed with the regular save process
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete associated files when the instance is deleted."""
        for field in self._get_file_fields():
            self._delete_file(getattr(self, field))

        # Call the parent class delete method
        super().delete(*args, **kwargs)


class SequenceField(models.Model):
    seq_number = models.BigIntegerField(blank=True, null=True, db_index=True, editable=False)

    objects = SequenceManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Only generate sequence if creating a new object
        if self._state.adding and self.seq_number is None:
            self.seq_number = self._generate_sequence_number()
        super().save(*args, **kwargs)

    def _generate_sequence_number(self):
        """
        Thread-safe sequence generation using PostgreSQL sequences.
        """
        sequence_name = f"{self._meta.app_label}_{self._meta.model_name.lower()}_seq_number"

        with connection.cursor() as cursor:
            # Create sequence if it doesn't exist
            cursor.execute(f"CREATE SEQUENCE IF NOT EXISTS {sequence_name} START 1;")
            # Get next value atomically
            cursor.execute(f"SELECT nextval('{sequence_name}')")
            next_seq = cursor.fetchone()[0]

        return next_seq


class PermissionModelBase(models.base.ModelBase):
    DEFAULT_ACTIONS = ["view", "add", "change", "delete"]

    def __new__(cls, name, bases, attrs):
        meta = attrs.get("Meta", None)

        # Collect permissions safely
        generated_permissions = []

        # -------------------------------------------------
        # 1 Only add custom permissions (NOT CRUD)
        # -------------------------------------------------
        perms_class = attrs.get("Permissions", None)

        if perms_class:
            for attr_name, value in perms_class.__dict__.items():
                if not attr_name.startswith("_"):
                    codename = f"{value}_{name.lower()}"
                    label = f"Can {value} {name.lower()}s"
                    generated_permissions.append((codename, label))

        # -------------------------------------------------
        # 2 Inject into Meta without overriding existing
        # -------------------------------------------------
        if generated_permissions:
            if meta:
                existing = getattr(meta, "permissions", [])
                meta.permissions = list(existing) + generated_permissions
            else:
                class Meta:
                    permissions = generated_permissions
                attrs["Meta"] = Meta

        return super().__new__(cls, name, bases, attrs)


class PermissionModel(models.Model, metaclass=PermissionModelBase):
    class Meta:
        abstract = True


class BaseModel(SerializesModels, UUIDModel, TimeStampedModel, DirtyFields, FileFields, PermissionModel):

    class Meta:
        abstract = True

    def _serialize_value(self, value: Any) -> Any:
        """
        Converts Python types, dates, decimals, and files into JSON primitives.
        """
        if value is None:
            return None
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, Promise):  # Safe handling of lazy translations
            return str(value)
        
        # Safe evaluation of FileField/ImageField URLs
        if hasattr(value, "url"):
            try:
                return value.url if value else None
            except ValueError:
                return None
                
        return value

    def to_dict(
        self, 
        include: set[str] | list[str] | None = None, 
        exclude: set[str] | list[str] | None = None, 
        depth: int = 0, 
        max_depth: int = 1, 
        include_m2m: bool = False
    ) -> dict[str, Any]:
        """
        Serializes the model instance into a dictionary representation.
        Optimized to strictly avoid unnecessary database evaluations.
        """
        data = {}
        exclude_set = set(exclude or [])
        include_set = set(include) if include else None

        # 1. Standard and Forward Relationship Fields
        for field in self._meta.fields:
            field_name = field.name

            if (include_set and field_name not in include_set) or (field_name in exclude_set):
                continue

            # ---------- ForeignKey / OneToOne Fields ----------
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                # OPTIMIZATION: Read the DB attribute name directly (e.g., 'customer_id')
                # to prevent Django from executing a SQL query to load the related model.
                db_value = getattr(self, field.attname)

                if db_value is None:
                    data[field_name] = None
                    continue

                if depth < max_depth:
                    try:
                        # Only hit the DB to resolve the instance if we intend to recurse
                        relation_instance = getattr(self, field_name)
                    except Exception:  # Catches RelatedObjectDoesNotExist
                        data[field_name] = None
                        continue

                    if relation_instance and hasattr(relation_instance, "to_dict"):
                        data[field_name] = relation_instance.to_dict(
                            depth=depth + 1,
                            max_depth=max_depth,
                        )
                    else:
                        data[field_name] = self._serialize_value(db_value)
                else:
                    # If we don't recurse, return the raw ID/PK immediately (0 DB queries)
                    data[field_name] = self._serialize_value(db_value)

            # ---------- Standard Local Fields ----------
            else:
                try:
                    value = getattr(self, field_name)
                except Exception:
                    data[field_name] = None
                    continue
                data[field_name] = self._serialize_value(value)

        # ---------- Refined ManyToMany Fields ----------
        if include_m2m:
            for field in self._meta.many_to_many:
                if (include_set and field.name not in include_set) or (field.name in exclude_set):
                    continue

                # OPTIMIZATION: Check if M2M objects are already prefetched to prevent N+1 hits
                prefetched_cache = getattr(self, "_prefetched_objects_cache", {})
                if field.name in prefetched_cache:
                    queryset = prefetched_cache[field.name]
                    # Since it is already loaded in memory, read `.pk` from the active instances
                    data[field.name] = [self._serialize_value(obj.pk) for obj in queryset]
                else:
                    # OPTIMIZATION: If not prefetched, use .values_list('pk') to run a lightning-fast
                    # query that pulls *only* the primary keys, avoiding model instantiation overhead.
                    data[field.name] = [
                        self._serialize_value(pk)
                        for pk in getattr(self, field.name).values_list("pk", flat=True)
                    ]

        return data

    def to_json(self, indent: int | None = None, **kwargs) -> str:
        """
        Returns a JSON string representation of the model.
        Accepts all argument filters supported by to_dict.
        """
        dict_args = {
            "include": kwargs.pop("include", None),
            "exclude": kwargs.pop("exclude", None),
            "depth": kwargs.pop("depth", 0),
            "max_depth": kwargs.pop("max_depth", 1),
            "include_m2m": kwargs.pop("include_m2m", False),
        }
        
        data = self.to_dict(**dict_args)
        return json.dumps(data, cls=ModelJSONEncoder, indent=indent)
    
    
class TaskMixin(models.Model):
    task_id = models.CharField(max_length=200, blank=True, null=True)
    task_url = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        abstract = True
    
    def sync_task_id(self, task_id):
        self.task_id = task_id
        self.save()
        
    def sync_task_url(self, task_url):
        self.task_url = task_url
        self.save()


class OptionModel(BaseModel, SequenceField):
    SEPARATOR = "_"
    name = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["seq_number"]

    def __str__(self) -> str:
        if self.description:
            return self.description
        else:
            return self.value

    
    def __getattr__(self, name):
        option = self.get_option(name)
        return option
    
    def equals(self, option):
        if isinstance(option, OptionModel):
            return self.pk == option.pk
        elif isinstance(option, str):
            if self.name.lower() == option.lower():
                return True
            
            try:
                option_instance = self.get_option(option)
                if isinstance(option_instance, OptionModel):
                    return self.pk == option_instance.pk
                else:
                    # Handle the case where option_instance is not an OptionModel
                    raise ValueError(f"The provided option '{option}' is not a valid OptionModel instance.")
            except Exception as e:
                # Handle potential errors from get_option method
                raise ValueError(f"Error getting option instance: {e}")
        else:
            # If option is neither OptionModel nor string
            raise TypeError(f"Expected OptionModel or string, got {type(option).__name__} instead.")

    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, separator=self.SEPARATOR)
        self.name = str(self.name).upper()
        if not self.value:
            # Convert NAME_CONSTANT to human-readable value
            self.value = self.name.replace("_", " ").title()
        super().save(*args, **kwargs)

    @classmethod
    def get_option(cls, name):
        # Attempt to find an object by name
        instance = cls.objects.filter(name=name).first()

        if instance:
            return instance

        # If not found, try to find by slug
        instance = cls.objects.filter(slug=name).first()

        if instance:
            return instance
        
        # If not found, try to find by code
        instance = cls.objects.filter(code=name).first()

        if instance:
            return instance

        # If still not found, generate slug and search again
        slug = slugify(name, separator=cls.SEPARATOR)
        instance = cls.objects.filter(slug=slug).first()

        if instance:
            return instance

        # If no instance is found, raise an AttributeError
        raise AttributeError(f"{cls.__name__} object has no option '{name}'")

    @classmethod
    def get_value(cls, name):
        option = cls.get_option(name)
        return option.value
    
    @classmethod
    def get_choices(cls):
        return cls.objects.all()
    
    @classmethod
    def get_active_choices(cls):
        return cls.objects.filter(is_visible=True)


class Versionable(BaseModel):
    version_number = models.CharField(max_length=20, help_text="Version number should be in the form 'X.Y.Z' (example: 1.0.0)")
    version_year = models.CharField(max_length=100, blank=True, null=True)
    effective_from = models.DateField(blank=True, null=True)
    effective_to = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True  # Mark this as an abstract class

    @property
    def version_text(self):
        if not self.version_year:
            return f"{self.version_number}"
        return f"{self.version_year}.{self.version_number}"

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def get_latest(cls, exclude_pk=None, **kwargs):
        
        queryset = cls.objects.filter(**kwargs).exclude(version_number__isnull=True)
        
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)

        all_versions = list(queryset)

        if not all_versions:
            return None

        try:
            # Sort using semver-aware comparison
            all_versions.sort(
                key=lambda obj: semver.VersionInfo.parse(obj.version_number),
                reverse=True
            )
            return all_versions[0]
        except ValueError as e:
            raise ValidationError(f"Invalid version format found in database: {e}")

    def clean(self):
        """
        Custom validation to ensure version follows the correct format.
        """
        if self.version_number:
            try:
                # Parse the version to check if it"s valid
                semver.VersionInfo.parse(self.version_number)
            except ValueError:
                raise ValidationError(f"Version {self.version_number} is not a valid semantic version. It should be in the form 'X.Y.Z' ")
    
    def activate(self):
        self.is_active = True
        self.save()

    def deactivate(self):
        self.is_active = False
        self.save()
    
    def get_previous(self, index=0):
        previous = self.__class__.objects.filter(created__lt=self.created).order_by("-created")
        try:
            if index < len(previous):
                return previous[index]
        except IndexError:
            pass
        return None
    
    def increment_version(self, bump_type="patch"):
        """
        Increment the version based on the bump_type.
        :param bump_type: str, one of ["major", "minor", "patch"]
        """
        kwargs = self.get_version_filter()
        try:
            latest_record = self.__class__.get_latest(exclude_pk=self.pk, **kwargs)
            if latest_record:
                current_version = semver.VersionInfo.parse(latest_record.version_number)
                if bump_type == "major":
                    self.version_number = current_version.bump_major()
                elif bump_type == "minor":
                    self.version_number = current_version.bump_minor()
                else:  # default to patch bump
                    self.version_number = current_version.bump_patch()
            else:
                self.version_number = "1.0.0"  # Start with the initial version if no previous version exists
        except Exception as e:
            raise ValidationError(f"Error incrementing version: {str(e)}")

    def get_version_filter(self):
        """
        Define the filter criteria for determining the latest version.
        Override this in subclasses to customize the filter criteria.
        """
        return {}

    def save(self, *args, **kwargs):
        # Allow manual version override, but still run validation
        if not self.version_number:
            self.increment_version(kwargs.pop("bump_type", "patch"))

        # Run the custom validation before saving
        self.full_clean()  # Calls the clean() method

        super().save(*args, **kwargs)


class BaseConfig(UUIDModel):
    DATA_TYPE_CHOICES = [
        ("text", "Text"),
        ("number", "Number"),
        ("decimal", "Decimal"),
        ("boolean", "Boolean"),
        ("list", "List"),
        ("date", "Date"),
        ("datetime", "DateTime"),
        ("time", "Time"),
    ]

    name = models.CharField(max_length=255, unique=True, help_text="Configuration item name, must be unique")
    label = models.CharField(max_length=255, blank=True, null=True,help_text="Optional display label for this setting")
    value = models.CharField(max_length=255, blank=True, null=True, help_text="Current configuration value, modifiable by the user")
    type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES, help_text="Data type acceptable for this configuration item")
    default = models.CharField(max_length=255, blank=True, null=True, help_text="Default value if configuration value is empty or nullable")
    options = models.JSONField(default=dict, null=True, blank=True, help_text="Acceptable values for the configuration item (as a dictionary)")
    group = models.CharField(max_length=255, blank=True, null=True, help_text="Group name to organize related settings")

    class Meta:
        abstract = True

    @property
    def setting_value(self):
        return self.get_effective_value()

    def __str__(self):
        return f"{self.name} ({self.type})"
    
    def save(self, *args, **kwargs):
        # Set the label if it"s empty, using the name field as a basis
        if not self.label and self.name:
            # You can customize this label generation logic as needed
            self.label = re.sub(r"[_-]", " ", self.name).title()  # Replaces undersdjangospices/dashes with spaces and capitalizes the words   
        super().save(*args, **kwargs)

    def get_display_name(self):
        """Return the label if available, otherwise fall back to the name."""
        return self.label if self.label else self.name

    def parse_value(self, value, data_type):
        """Parse the value based on the data type."""
        if data_type == "number":
            return int(value)
        if data_type == "decimal":
            return Decimal(value)
        elif data_type == "boolean":
            return str(value).lower() in ["true", "1", "yes"]
        elif data_type == "list":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        elif data_type == "date":
            return datetime.strptime(value, "%Y-%m-%d").date()
        elif data_type == "datetime":
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        elif data_type == "time":
            return datetime.strptime(value, "%H:%M:%S").time()
        return value

    def format_value(self, value, data_type):
        """Format the value to a string representation based on the data type."""
        if data_type in ["date", "datetime", "time"]:
            return value.isoformat() if isinstance(value, (date, datetime, time)) else str(value)
        return str(value)

    def get_effective_value(self):
        """Returns the current value or default if the value is not set."""
        return self.get_value() if self.value else self.get_default_value()

    def get_value(self):
        """Parse the value field based on its type."""
        if not self.value:
            return None
        return self.parse_value(self.value, self.type)

    def get_default_value(self):
        """Parse the default field based on its type."""
        if not self.default:
            return None
        return self.parse_value(self.default, self.type)

    def get_options(self):
        """Retrieve acceptable options as a dictionary."""
        return self.options or {}

    def has_options(self):
        """Check if the setting has predefined options."""
        return bool(self.options)

    def get_option_value(self, option):
        """Retrieve the value of a specific option key."""
        return self.get_options().get(option)

    def set_value(self, value):
        """Set the value and ensure its formatted correctly for storage."""
        self.value = self.format_value(value, self.type)
        self.save()

    def set_default_value(self, value):
        """Set the default value and ensure its formatted correctly for storage."""
        self.default = self.format_value(value, self.type)
        self.save()

