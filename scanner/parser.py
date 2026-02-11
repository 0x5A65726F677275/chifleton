"""Parse dependency files (requirements.txt and pyproject.toml [project.dependencies])."""

import re
from pathlib import Path
from typing import NamedTuple

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


class ParsedDependency(NamedTuple):
    """A single parsed dependency: name, optional version, and optional ecosystem (PyPI/npm)."""

    name: str
    version: str | None
    ecosystem: str | None = None


# Match: package==version, package>=x, package~=x, package<=x, package, or package (comment)
REQUIREMENT_LINE = re.compile(
    r"^\s*([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*"
    r"(?:==|>=|<=|!=|~=|<|>)\s*"
    r"([a-zA-Z0-9.*+!\-]+)?\s*"
    r"(?:#.*)?$"
)
# Fallback: package only (no version operator)
REQUIREMENT_NAME_ONLY = re.compile(r"^\s*([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*(?:#.*)?$")


def parse_requirements(content: str) -> list[ParsedDependency]:
    """
    Parse requirements.txt-style content into (name, version) pairs.
    Ignores comments, empty lines, and options (-e, -r, etc.).
    """
    deps: list[ParsedDependency] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-") and not line.startswith("--"):
            continue
        # Normalize: remove inline comments for parsing
        if "#" in line:
            line = line[: line.index("#")].strip()
        # Try package==version (or other operators)
        m = REQUIREMENT_LINE.match(line)
        if m:
            name = m.group(1)
            version = m.group(2) or None
            if version:
                deps.append(ParsedDependency(name=name, version=version))
            else:
                deps.append(ParsedDependency(name=name, version=None))
            continue
        m = REQUIREMENT_NAME_ONLY.match(line)
        if m:
            deps.append(ParsedDependency(name=m.group(1), version=None))
    return deps


def parse_requirements_file(path: Path) -> list[ParsedDependency]:
    """Read and parse a requirements file from disk."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_requirements(text)


def parse_pyproject_file(path: Path) -> list[ParsedDependency]:
    """
    Read a pyproject.toml and extract [project.dependencies] as ParsedDependency list.
    Each dependency string (e.g. "click>=8.0") is parsed with requirements-style logic.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    data = tomllib.loads(text)
    project = data.get("project") or {}
    raw_deps = project.get("dependencies")
    if not isinstance(raw_deps, list):
        return []
    deps: list[ParsedDependency] = []
    for item in raw_deps:
        if not isinstance(item, str):
            continue
        # Parse one line (e.g. "click>=8.0"); parse_requirements handles one line
        parsed = parse_requirements(item.strip())
        deps.extend(parsed)
    return deps


# Pip freeze format: exactly "name==version" per line (or -e / # ...)
FREEZE_LINE = re.compile(r"^\s*([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*==\s*([a-zA-Z0-9.*+!\-]+)\s*$")


def parse_freeze(content: str) -> list[ParsedDependency]:
    """
    Parse pip-freeze style output (e.g. from `pip freeze` or `pip list --format=freeze`).
    Only accepts lines of the form "name==version". Skips -e, comments, empty lines.
    """
    deps: list[ParsedDependency] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-e ") or line.startswith("-e\t"):
            continue
        m = FREEZE_LINE.match(line)
        if m:
            deps.append(ParsedDependency(name=m.group(1), version=m.group(2)))
    return deps


def parse_dependency_file(path: Path) -> list[ParsedDependency]:
    """Parse a dependency file: requirements.txt or pyproject.toml ([project.dependencies])."""
    if path.name == "pyproject.toml":
        return parse_pyproject_file(path)
    return parse_requirements_file(path)
