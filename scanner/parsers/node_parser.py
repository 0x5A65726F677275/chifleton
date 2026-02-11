"""Node.js ecosystem: package.json, package-lock.json, yarn.lock, pnpm-lock.yaml."""

import json
import re
from pathlib import Path
from typing import Any

from scanner.parser import ParsedDependency

# npm v7+ lockfile: "packages" map with "node_modules/pkg" -> { "version": "1.2.3" }
# npm v6: "dependencies" nested tree with .version
# yarn.lock: line-oriented, "pkg@version:" then "  version \"x.y.z\""
# pnpm: YAML with packages block


def _norm_package_key(key: str) -> str:
    """From lockfile key like node_modules/foo or node_modules/foo/bar return package name."""
    key = key.replace("node_modules/", "").strip()
    if not key:
        return ""
    return key.split("/")[0]


def parse_package_lock(path: Path) -> list[ParsedDependency]:
    """
    Parse package-lock.json (npm v7+ format with "packages").
    Returns (name, version) for all packages in the lockfile; ecosystem is npm.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(text)
    packages = data.get("packages")
    if packages is not None and isinstance(packages, dict):
        # npm v7+ format
        seen: set[tuple[str, str]] = set()
        deps: list[ParsedDependency] = []
        for key, pkg in packages.items():
            if key == "" or not isinstance(pkg, dict):
                continue
            version = pkg.get("version")
            if not version or not isinstance(version, str):
                continue
            name = _norm_package_key(key)
            if not name or (name, version) in seen:
                continue
            seen.add((name, version))
            deps.append(ParsedDependency(name=name, version=version, ecosystem="npm"))
        return deps
    # npm v6: dependencies tree
    return _parse_package_lock_v6(data)


def _parse_package_lock_v6(data: dict[str, Any]) -> list[ParsedDependency]:
    """Parse npm v6 package-lock.json (dependencies tree)."""
    seen: set[tuple[str, str]] = set()
    deps: list[ParsedDependency] = []

    def walk(node: dict[str, Any], prefix: str) -> None:
        if not isinstance(node, dict):
            return
        for key, val in node.items():
            if not isinstance(val, dict):
                continue
            version = val.get("version")
            if version and isinstance(version, str):
                name = key
                if (name, version) not in seen:
                    seen.add((name, version))
                    deps.append(ParsedDependency(name=name, version=version, ecosystem="npm"))
            nested = val.get("dependencies")
            if isinstance(nested, dict):
                walk(nested, f"{prefix}{key}/")

    root = data.get("dependencies")
    if isinstance(root, dict):
        walk(root, "")
    return deps


def parse_package_json(path: Path) -> list[ParsedDependency]:
    """
    Parse package.json and return direct dependencies (dependencies + devDependencies).
    Versions may be ranges (^1.2.0); we use the range as-reported for declared-only scanning.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(text)
    deps: list[ParsedDependency] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        raw = data.get(section)
        if not isinstance(raw, dict):
            continue
        for name, version in raw.items():
            if not isinstance(version, str):
                version = ""
            # Normalize: strip workspace: or other protocols for display
            version = version.strip()
            deps.append(ParsedDependency(name=name, version=version or None, ecosystem="npm"))
    return deps


def parse_yarn_lock(path: Path) -> list[ParsedDependency]:
    """
    Parse yarn.lock (classic format). Each block starts with "pkg@version:" and
    has a line "  version \"x.y.z\"" for the resolved version.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    seen: set[tuple[str, str]] = set()
    deps: list[ParsedDependency] = []
    # Match block start: "pkg@version:" or "pkg@npm:version:"
    block_start = re.compile(r"^([^@\s]+)@(?:npm:)?(.+):\s*$")
    version_line = re.compile(r'^\s+version\s+"([^"]+)"\s*$')
    current_name: str | None = None
    current_key: str = ""
    for line in text.splitlines():
        m = block_start.match(line)
        if m:
            current_name = m.group(1).strip('"')
            current_key = m.group(2).strip('"')
            continue
        vm = version_line.match(line)
        if vm and current_name is not None:
            version = vm.group(1)
            if (current_name, version) not in seen:
                seen.add((current_name, version))
                deps.append(ParsedDependency(name=current_name, version=version, ecosystem="npm"))
            current_name = None
            current_key = ""
    return deps


def parse_pnpm_lock(path: Path) -> list[ParsedDependency]:
    """
    Parse pnpm-lock.yaml. Format: packages section with entries like
      /lodash/4.17.21:
        version: 4.17.21
    or similar. We need to parse YAML.
    """
    try:
        import yaml
    except ImportError:
        # Fallback: minimal YAML parsing for packages block
        return _parse_pnpm_lock_fallback(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return []
    packages = data.get("packages") or data.get("snapshots")
    if not isinstance(packages, dict):
        return []
    seen: set[tuple[str, str]] = set()
    deps: list[ParsedDependency] = []
    for key, val in packages.items():
        if not isinstance(val, dict):
            continue
        version = val.get("version")
        if not version:
            # pnpm sometimes has /pkg/version as key
            if key.startswith("/"):
                parts = key.strip("/").rsplit("/", 1)
                if len(parts) == 2:
                    name, version = parts[0], parts[1]
                else:
                    continue
            else:
                continue
        if isinstance(version, dict):
            version = version.get("version") or version.get("tarball")
        if not isinstance(version, str):
            continue
        name = key.strip("/").split("/")[0] if key.startswith("/") else key.split("/")[0]
        if (name, version) not in seen:
            seen.add((name, version))
            deps.append(ParsedDependency(name=name, version=version, ecosystem="npm"))
    return deps


def _parse_pnpm_lock_fallback(path: Path) -> list[ParsedDependency]:
    """Simple regex-based parse for pnpm-lock.yaml when PyYAML not installed."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # Match /name/version: or name@version: then version: x.y.z
    seen: set[tuple[str, str]] = set()
    deps: list[ParsedDependency] = []
    in_packages = False
    current_name: str | None = None
    for line in text.splitlines():
        if line.strip() == "packages:" or line.strip().startswith("packages:"):
            in_packages = True
            continue
        if in_packages and line and not line[0].isspace():
            in_packages = False
        if not in_packages:
            continue
        # Entry like "  /lodash/4.17.21:" or "  lodash@4.17.21:"
        stripped = line.strip()
        if stripped.endswith(":"):
            key = stripped[:-1].strip()
            if key.startswith("/"):
                parts = key.strip("/").split("/")
                if len(parts) >= 2:
                    current_name = parts[0]
            elif "@" in key:
                current_name, _ = key.split("@", 1)
        if "version:" in line and current_name:
            # "    version: 4.17.21"
            v = line.split("version:", 1)[-1].strip().strip("'\"").strip()
            if v and (current_name, v) not in seen:
                seen.add((current_name, v))
                deps.append(ParsedDependency(name=current_name, version=v, ecosystem="npm"))
            current_name = None
    return deps


def get_deps_node(path: Path) -> tuple[list[ParsedDependency], str, bool]:
    """
    Parse Node dependency file or directory. Returns (deps, input_label, from_lockfile).
    When path is a directory, looks for package-lock.json, then yarn.lock, then pnpm-lock.yaml, then package.json.
    """
    if path.is_file():
        if path.name == "package-lock.json":
            return parse_package_lock(path), str(path), True
        if path.name == "yarn.lock":
            return parse_yarn_lock(path), str(path), True
        if path.name == "pnpm-lock.yaml":
            return parse_pnpm_lock(path), str(path), True
        if path.name == "package.json":
            # Prefer sibling lockfile if present
            parent = path.parent
            for lock in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
                lock_path = parent / lock
                if lock_path.exists():
                    deps, _, from_lock = get_deps_node(lock_path)
                    return deps, str(lock_path), True
            return parse_package_json(path), str(path), False
        return [], str(path), False

    if path.is_dir():
        for name in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "package.json"):
            candidate = path / name
            if candidate.exists():
                return get_deps_node(candidate)
    return [], str(path), False
