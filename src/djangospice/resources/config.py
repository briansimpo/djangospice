from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ResourceConfig:
    """
    Configuration settings for resource export and formatting.

    Attributes:
        export_data (bool): Flag indicating if data should be exported.
        protect (bool): Flag indicating if the exported sheet/data should be protected.
        hidden_fields (List[str]): List of field names that should be hidden during export.
        export_name (Optional[str]): Custom name for the export sheet or file.
    """
    export_data: bool = False
    protect: bool = True
    hidden_fields: List[str] = field(default_factory=list)
    export_name: Optional[str] = None
