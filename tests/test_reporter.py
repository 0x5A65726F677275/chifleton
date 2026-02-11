"""Tests for reporter: HTML and JSON output structure and content."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scanner.reporter import (
    report_html,
    report_json,
    _enrich_results,
    _overview_rows,
    _vuln_status,
)


def test_enrich_results_empty() -> None:
    assert _enrich_results([]) == []


def test_enrich_results_no_vulns() -> None:
    results = [{"name": "pkg", "version": "1.0", "vulns": []}]
    enriched = _enrich_results(results)
    assert len(enriched) == 1
    assert enriched[0]["name"] == "pkg"
    assert enriched[0]["version"] == "1.0"
    assert enriched[0]["vuln_count"] == 0
    assert enriched[0]["vulns"] == []


def test_enrich_results_with_vulns() -> None:
    results = [
        {
            "name": "foo",
            "version": "2.0",
            "vulns": [
                {"id": "CVE-2020-1", "summary": "A bug", "references": [{"url": "https://example.com"}]},
            ],
        }
    ]
    enriched = _enrich_results(results)
    assert len(enriched) == 1
    assert enriched[0]["vuln_count"] == 1
    assert len(enriched[0]["vulns"]) == 1
    assert enriched[0]["vulns"][0]["ids"]  # at least CVE-2020-1
    assert "CVE-2020-1" in enriched[0]["vulns"][0]["ids"]
    assert enriched[0]["vulns"][0]["references"] == ["https://example.com"]


def test_report_html_contains_summary_and_footer(tmp_path: Path) -> None:
    results = [
        {"name": "a", "version": "1.0", "vulns": []},
        {"name": "b", "version": "2.0", "vulns": [{"id": "OSV-1", "summary": "Issue"}]},
    ]
    out = tmp_path / "report.html"
    report_html(
        results,
        out,
        report_author="Test Author",
        scanner_version="0.2.0",
    )
    html = out.read_text(encoding="utf-8")
    assert "Packages scanned" in html
    assert "With vulnerabilities" in html
    assert "Total vulnerabilities" in html
    assert "Chifleton" in html
    assert "Test Author" in html
    assert "0.2.0" in html
    assert "UTC" in html
    assert "Vulnerabilities" in html
    assert "Packages" in html
    assert "a" in html and "b" in html


def test_report_json_structure(tmp_path: Path) -> None:
    results = [
        {"name": "pkg", "version": "1.0", "vulns": [{"id": "CVE-X", "summary": "X"}]},
    ]
    out = tmp_path / "report.json"
    report_json(
        results,
        out,
        report_author="Test Author",
        scanner_version="0.2.0",
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "report" in data
    assert "packages" in data
    r = data["report"]
    assert "generated_at" in r
    assert "scanner_version" in r
    assert r["scanner_version"] == "0.2.0"
    assert r["report_author"] == "Test Author"
    assert r["package_count"] == 1
    assert r["vulnerable_package_count"] == 1
    assert r["total_vulnerabilities"] == 1
    assert len(data["packages"]) == 1
    assert data["packages"][0]["name"] == "pkg"
    assert data["packages"][0]["vuln_count"] == 1
    assert len(data["packages"][0]["vulns"]) == 1
    assert data["packages"][0]["vulns"][0]["id"] == "CVE-X"
    assert "status" in data["packages"][0]["vulns"][0]
    assert data["packages"][0]["vulns"][0]["status"] == "Active"


def test_vuln_status_withdrawn() -> None:
    vuln = {"id": "CVE-1", "withdrawn": "2024-01-15T00:00:00Z"}
    assert _vuln_status(vuln, "1.0") == "Withdrawn"


def test_vuln_status_fixed_via_affected_events() -> None:
    vuln = {
        "id": "CVE-2",
        "published": "2023-01-01T00:00:00Z",
        "affected": [
            {
                "ranges": [
                    {"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "2.0.0"}]}
                ]
            }
        ],
    }
    assert _vuln_status(vuln, "2.0.0") == "Fixed"
    assert _vuln_status(vuln, "3.0.0") == "Fixed"
    assert _vuln_status(vuln, "1.0.0") == "Active"


def test_vuln_status_active() -> None:
    vuln = {"id": "CVE-3", "published": "2023-06-01T00:00:00Z"}
    assert _vuln_status(vuln, "1.0") == "Active"


def test_vuln_status_unknown() -> None:
    vuln = {}
    assert _vuln_status(vuln, "1.0") == "Unknown"


def test_overview_rows_status_values() -> None:
    enriched = [
        {
            "name": "pkg",
            "version": "1.0",
            "vulns": [
                {"ids": ["GHSA-x"], "severity": "High", "published": "2023-01-01", "withdrawn": None, "affected": None, "database_specific": None},
                {"ids": ["GHSA-y"], "severity": "Medium", "published": None, "withdrawn": "2024-01-01", "affected": None, "database_specific": None},
            ],
        }
    ]
    rows = _overview_rows(enriched)
    assert len(rows) == 2
    assert rows[0]["status"] == "Active"
    assert rows[1]["status"] == "Withdrawn"


def test_report_json_empty_vulns(tmp_path: Path) -> None:
    results = [{"name": "safe", "version": "1.0", "vulns": []}]
    out = tmp_path / "report.json"
    report_json(results, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["report"]["total_vulnerabilities"] == 0
    assert data["report"]["vulnerable_package_count"] == 0
    assert data["packages"][0]["vulns"] == []
