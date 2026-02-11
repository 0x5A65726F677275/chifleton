"""Python ecosystem: requirements.txt, pyproject.toml, pip-freeze."""

from pathlib import Path

from scanner.parser import (
    ParsedDependency,
    parse_dependency_file,
    parse_freeze,
    parse_requirements_file,
    parse_pyproject_file,
)


def get_deps_from_file(path: Path) -> list[ParsedDependency]:
    """Parse a Python dependency file; return list with ecosystem set to PyPI."""
    deps = parse_dependency_file(path)
    return [d._replace(ecosystem="PyPI") if d.ecosystem is None else d for d in deps]


def get_deps_from_freeze(content: str) -> list[ParsedDependency]:
    """Parse pip-freeze style content; return list with ecosystem set to PyPI."""
    deps = parse_freeze(content)
    return [d._replace(ecosystem="PyPI") if d.ecosystem is None else d for d in deps]
