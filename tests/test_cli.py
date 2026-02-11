"""End-to-end tests for the CLI: exit codes, output files, and report content."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from scanner.cli import cli


def test_cli_scan_file_not_found() -> None:
    """Scan with missing file should exit with 1."""
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", "/nonexistent/requirements.txt", "--no-cache"])
    assert result.exit_code == 1


def test_cli_scan_empty_requirements_exits_zero(tmp_path: Path) -> None:
    """Scan with empty requirements (no deps) should complete without error."""
    req = tmp_path / "requirements.txt"
    req.write_text("# empty\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", str(req), "--no-cache"])
    assert result.exit_code == 0


def test_cli_scan_produces_html_and_json(tmp_path: Path) -> None:
    """With mocked OSV, scan produces HTML and JSON when requested."""
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.28.0\n")
    html_path = tmp_path / "scan-report.html"
    json_path = tmp_path / "scan-report.json"

    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": []}):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", str(req), "--report", "html", "--no-cache"])
    assert result.exit_code == 0
    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    assert "Packages scanned" in html
    assert "Chifleton" in html

    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": []}):
        runner.invoke(cli, ["scan", str(req), "--report", "json", "--no-cache"])
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "report" in data and "packages" in data
    assert data["report"]["package_count"] == 1


def test_cli_scan_pyproject_toml(tmp_path: Path) -> None:
    """Scan pyproject.toml produces reports when requested."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\ndependencies = [\"requests>=2.28\"]\n")
    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": []}):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", str(pyproject), "--report", "json", "--no-cache"])
    assert result.exit_code == 0
    data = json.loads((tmp_path / "scan-report.json").read_text(encoding="utf-8"))
    assert data["report"]["package_count"] == 1
    assert data["packages"][0]["name"] == "requests"


def test_cli_scan_with_vulns_in_report(tmp_path: Path) -> None:
    """With mocked vulns, HTML and JSON contain vulnerability info."""
    req = tmp_path / "requirements.txt"
    req.write_text("vulnpkg==1.0\n")
    mock_vulns = [
        {
            "id": "CVE-TEST-123",
            "summary": "Test vulnerability",
            "references": [{"url": "https://example.com/cve"}],
        }
    ]

    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": mock_vulns}):
        runner = CliRunner()
        runner.invoke(cli, ["scan", str(req), "--report", "html", "--no-cache"])
    html = (tmp_path / "scan-report.html").read_text(encoding="utf-8")
    assert "CVE-TEST-123" in html
    assert "Total vulnerabilities" in html

    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": mock_vulns}):
        runner.invoke(cli, ["scan", str(req), "--report", "json", "--no-cache"])
    data = json.loads((tmp_path / "scan-report.json").read_text(encoding="utf-8"))
    assert data["report"]["total_vulnerabilities"] == 1
    assert any(v.get("id") == "CVE-TEST-123" for p in data["packages"] for v in p["vulns"])


def test_cli_scan_from_freeze_file(tmp_path: Path) -> None:
    """--from-freeze with a file parses name==version and writes reports to that dir."""
    freeze_file = tmp_path / "frozen.txt"
    freeze_file.write_text("requests==2.31.0\nJinja2==3.1.2\n")
    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": []}):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["scan", str(freeze_file), "--from-freeze", "--report", "json", "--no-cache"]
        )
    assert result.exit_code == 0
    data = json.loads((tmp_path / "scan-report.json").read_text(encoding="utf-8"))
    assert data["report"]["package_count"] == 2
    names = [p["name"] for p in data["packages"]]
    assert "requests" in names and "Jinja2" in names


def test_cli_scan_fail_on_vuln_exits_one(tmp_path: Path) -> None:
    """--fail-on-vuln exits 1 when vulnerabilities are found."""
    req = tmp_path / "requirements.txt"
    req.write_text("pkg==1.0\n")
    mock_vulns = [{"id": "CVE-2024-0000", "summary": "Test"}]
    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": mock_vulns}):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", str(req), "--report", "none", "--fail-on-vuln", "--no-cache"])
    assert result.exit_code == 1


def test_cli_scan_fail_on_vuln_exits_zero_when_clean(tmp_path: Path) -> None:
    """--fail-on-vuln exits 0 when no vulnerabilities."""
    req = tmp_path / "requirements.txt"
    req.write_text("pkg==1.0\n")
    with patch("scanner.cli.query_vulnerabilities", return_value={"vulns": []}):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", str(req), "--report", "none", "--fail-on-vuln", "--no-cache"])
    assert result.exit_code == 0
