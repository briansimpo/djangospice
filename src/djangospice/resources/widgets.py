from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from import_export.widgets import DateWidget as BaseDateWidget
from import_export.widgets import ForeignKeyWidget as BaseForeignKeyWidget


class DateWidget(BaseDateWidget):
    """
    Handles conversion between Excel serial dates, various string formats, 
    and Python date objects.
    """
    INPUT_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    EXCEL_BASE_DATE = datetime(1899, 12, 30)

    def clean(self, value, row=None, *args, **kwargs):
        if value in (None, "", "NULL"):
            return None

        if isinstance(value, (datetime, date)):
            return value.date() if isinstance(value, datetime) else value

        # Handle Excel Serial Numbers
        if isinstance(value, (int, float)):
            try:
                return (self.EXCEL_BASE_DATE + timedelta(days=float(value))).date()
            except Exception as e:
                raise ValidationError(f"Invalid Excel serial date '{value}': {e}")

        # Fallback to string parsing
        value = str(value).strip()
        for fmt in self.INPUT_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        return super().clean(value, row, *args, **kwargs)


class ForeignKeyWidget(BaseForeignKeyWidget):
    """
    A safer ForeignKey widget that returns None if a record isn't found
    instead of crashing the import process.
    """
    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        try:
            return super().clean(value, row, **kwargs)
        except self.model.DoesNotExist:
            return None
        
  