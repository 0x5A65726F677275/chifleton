"""Dependency file parsers for multiple ecosystems (Python, Node.js)."""

from scanner.parsers.base import ParsedDependency
from scanner.parsers.detect import detect_ecosystem, get_dependencies

__all__ = [
    "ParsedDependency",
    "detect_ecosystem",
    "get_dependencies",
]
