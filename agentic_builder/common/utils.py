from pathlib import Path


def get_project_root() -> Path:
    """
    Returns the root directory of the project (where .git is located).
    Walks up from the current working directory.
    If no .git found, defaults to CWD.
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()
