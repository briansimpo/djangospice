import uuid
import decimal
import json
from datetime import date, datetime
from typing import  Any


def convert(value: Any) -> Any:
    if value is None: return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, dict, set, tuple)):
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float, str)):
        return value
    return str(value)
