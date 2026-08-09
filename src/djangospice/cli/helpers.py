from pathlib import Path


def find_project_root(start_dir: Path = None) -> Path | None:
    """
    Walks up from start_dir until a folder containing manage.py is found.
    Returns the absolute path as a Path object or None if not found.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current_dir = start_dir.resolve()

    while True:
        manage_path = current_dir / "manage.py"
        if manage_path.exists():
            return current_dir

        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            # Reached filesystem root
            return None
        current_dir = parent_dir
