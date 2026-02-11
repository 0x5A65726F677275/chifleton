"""Tests for requirements.txt and pyproject.toml parser."""

import pytest
from pathlib import Path
from scanner.parser import (
    parse_requirements,
    parse_requirements_file,
    parse_pyproject_file,
    parse_dependency_file,
    parse_freeze,
    ParsedDependency,
)


def test_parse_empty() -> None:
    assert parse_requirements("") == []
    assert parse_requirements("\n\n") == []


def test_parse_comments_and_empty_lines() -> None:
    content = """
# comment
requests==2.28.0
# another
flask
"""
    deps = parse_requirements(content)
    assert len(deps) == 2
    assert deps[0] == ParsedDependency(name="requests", version="2.28.0")
    assert deps[1] == ParsedDependency(name="flask", version=None)


def test_parse_package_eq_version() -> None:
    content = "package==1.2.3"
    deps = parse_requirements(content)
    assert deps == [ParsedDependency(name="package", version="1.2.3")]


def test_parse_package_no_version() -> None:
    content = "package"
    deps = parse_requirements(content)
    assert deps == [ParsedDependency(name="package", version=None)]


def test_parse_inline_comment() -> None:
    content = "requests==2.28.0  # HTTP library"
    deps = parse_requirements(content)
    assert deps == [ParsedDependency(name="requests", version="2.28.0")]


def test_parse_skips_options() -> None:
    content = """
-r base.txt
-e git+https://...
package==1.0
"""
    deps = parse_requirements(content)
    assert deps == [ParsedDependency(name="package", version="1.0")]


def test_parse_requirements_file(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("click>=8.0\njinja2==3.1.0\n")
    deps = parse_requirements_file(req)
    assert len(deps) == 2
    assert deps[0].name == "click"
    assert deps[0].version == "8.0"
    assert deps[1].name == "jinja2"
    assert deps[1].version == "3.1.0"


def test_parse_pyproject_file_empty_project(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = \"test\"\n")
    assert parse_pyproject_file(pyproject) == []


def test_parse_pyproject_file_no_dependencies(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = \"pkg\"\nversion = \"1.0\"\n")
    assert parse_pyproject_file(pyproject) == []


def test_parse_pyproject_file_with_dependencies(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "myapp"
version = "0.1.0"
dependencies = [
    "click>=8.0",
    "requests>=2.28",
    "Jinja2>=3.1",
]
""")
    deps = parse_pyproject_file(pyproject)
    assert len(deps) == 3
    assert deps[0] == ParsedDependency(name="click", version="8.0")
    assert deps[1] == ParsedDependency(name="requests", version="2.28")
    assert deps[2] == ParsedDependency(name="Jinja2", version="3.1")


def test_parse_dependency_file_requirements(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("foo==1.0\n")
    deps = parse_dependency_file(req)
    assert deps == [ParsedDependency(name="foo", version="1.0")]


def test_parse_dependency_file_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\ndependencies = [\"bar>=2.0\"]\n")
    deps = parse_dependency_file(pyproject)
    assert deps == [ParsedDependency(name="bar", version="2.0")]


def test_parse_freeze_empty() -> None:
    assert parse_freeze("") == []
    assert parse_freeze("\n\n# comment\n") == []


def test_parse_freeze_name_eq_version() -> None:
    content = "requests==2.28.0\nJinja2==3.1.2\n"
    deps = parse_freeze(content)
    assert deps == [
        ParsedDependency(name="requests", version="2.28.0"),
        ParsedDependency(name="Jinja2", version="3.1.2"),
    ]


def test_parse_freeze_skips_editable() -> None:
    content = "-e git+https://github.com/foo/bar.git@v1.0#egg=bar\npkg==1.0\n"
    deps = parse_freeze(content)
    assert deps == [ParsedDependency(name="pkg", version="1.0")]


def test_parse_freeze_skips_comments_and_empty() -> None:
    content = "# pip freeze\nrequests==2.31.0\n\n# end\n"
    deps = parse_freeze(content)
    assert deps == [ParsedDependency(name="requests", version="2.31.0")]
