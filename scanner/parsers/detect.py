"""Ecosystem detection and dependency resolution for scan target."""

from pathlib import Path

from scanner.parser import ParsedDependency
from scanner.parsers.python_parser import get_deps_from_file, get_deps_from_freeze
from scanner.parsers.node_parser import get_deps_node


def detect_ecosystem(path: Path, ecosystem_override: str | None = None) -> str | None:
    """
    Detect ecosystem from path (file or directory). Returns "python", "node", or None.
    If ecosystem_override is "python" or "node", use that when the path is a directory.
    """
    if ecosystem_override and ecosystem_override.lower() in ("python", "node"):
        return ecosystem_override.lower()

    if path.is_file():
        name = path.name.lower()
        if name in ("requirements.txt", "pyproject.toml"):
            return "python"
        if name in ("package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
            return "node"
        return None

    if path.is_dir():
        node_files = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "package.json")
        python_files = ("requirements.txt", "pyproject.toml")
        for f in node_files:
            if (path / f).exists():
                return "node"
        for f in python_files:
            if (path / f).exists():
                return "python"
    return None


def resolve_path_for_scan(path: str | None, default_python: str = "requirements.txt") -> Path:
    """Resolve path to file or directory for scanning. Default for Python is requirements.txt in cwd."""
    if path is None:
        return Path.cwd() / default_python
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p


def get_dependencies(
    path: Path,
    ecosystem_override: str | None = None,
    from_freeze: bool = False,
    freeze_content: str | None = None,
) -> tuple[str, list[ParsedDependency], str, bool]:
    """
    Get dependencies for the given path. Returns (ecosystem, deps, input_label, from_lockfile).
    ecosystem is "PyPI" or "npm" for OSV. from_lockfile is True when Node used a lockfile.
    """
    if from_freeze and freeze_content is not None:
        deps = get_deps_from_freeze(freeze_content)
        return "PyPI", deps, "stdin" if path.name == "-" or str(path) == "-" else str(path), True

    resolved = path if path.exists() else path
    eco = detect_ecosystem(resolved, ecosystem_override)

    if eco == "node":
        deps, input_label, from_lockfile = get_deps_node(resolved)
        return "npm", deps, input_label, from_lockfile

    if eco == "python" or eco is None:
        # Default to Python when path is file that parser can handle
        if resolved.is_file():
            try:
                deps = get_deps_from_file(resolved)
                return "PyPI", deps, str(resolved), True
            except Exception:
                pass
        if resolved.is_dir():
            for name in ("requirements.txt", "pyproject.toml"):
                candidate = resolved / name
                if candidate.exists():
                    deps = get_deps_from_file(candidate)
                    return "PyPI", deps, str(candidate), True
        # Fallback: try as requirements.txt path
        if resolved.is_file() and resolved.suffix in (".txt", ".toml") or resolved.name == "pyproject.toml":
            deps = get_deps_from_file(resolved)
            return "PyPI", deps, str(resolved), True

    return "PyPI", [], str(path), False
