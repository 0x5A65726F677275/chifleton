"""Shared utilities for the scanner."""

from pathlib import Path


def resolve_path(path: str | None) -> Path:
    """Resolve path to a requirements file; default to requirements.txt in cwd."""
    if path is None:
        return Path.cwd() / "requirements.txt"
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p
