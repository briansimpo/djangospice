import json
from pathlib import Path


def write_manifest(path, *, js=None, css=None, apps=(), source_count=0):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 2,
        "js": {"main": js} if js else {},
        "css": {"main": css} if css else {},
        "apps": list(apps),
        "source_count": source_count,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def read_manifest(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
