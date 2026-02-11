"""Terminal and HTML reporting for scan results."""

import html as html_module
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console
from rich.table import Table

from scanner import __author__ as DEFAULT_REPORT_AUTHOR, __version__ as SCANNER_VERSION
from scanner.remediation import enrich_vuln_remediation
from scanner.recommendations import get_improvement_recommendations


def _markdown_headers_to_html(text: str, max_length: int = 8000) -> str:
    """
    Convert Markdown headings (###, ##, #) to HTML h3/h2/h1. Escape other content.
    Prevents raw Markdown from appearing in the report.
    """
    if not text or not text.strip():
        return ""
    text = text[:max_length]
    lines = text.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^####\s+", stripped):
            content = re.sub(r"^####\s+", "", stripped)
            out.append(f"<h4>{html_module.escape(content)}</h4>")
        elif re.match(r"^###\s+", stripped):
            content = re.sub(r"^###\s+", "", stripped)
            out.append(f"<h3>{html_module.escape(content)}</h3>")
        elif re.match(r"^##\s+", stripped):
            content = re.sub(r"^##\s+", "", stripped)
            out.append(f"<h2>{html_module.escape(content)}</h2>")
        elif re.match(r"^#\s+", stripped):
            content = re.sub(r"^#\s+", "", stripped)
            out.append(f"<h2>{html_module.escape(content)}</h2>")
        else:
            out.append(html_module.escape(line))
    return "\n".join(out)


def _short_summary(text: str, max_chars: int = 280) -> str:
    """Return first 1–2 sentences for readability, or truncated text."""
    if not text or not text.strip():
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    truncated = text[: max_chars + 1]
    last_period = truncated.rfind(". ")
    if last_period > max_chars // 2:
        return truncated[: last_period + 1].strip()
    return truncated.rstrip() + "…"


def _vuln_ids(vuln: dict[str, Any]) -> list[str]:
    """Extract CVE/OSV IDs and aliases from a vulnerability."""
    ids = []
    if vuln.get("id"):
        ids.append(vuln["id"])
    for a in vuln.get("aliases") or []:
        if a and a not in ids:
            ids.append(a)
    return ids


def _vuln_refs(vuln: dict[str, Any]) -> list[str]:
    """Extract reference URLs from a vulnerability."""
    refs = []
    for r in vuln.get("references") or []:
        if isinstance(r, dict) and r.get("url"):
            refs.append(r["url"])
        elif isinstance(r, str):
            refs.append(r)
    return refs


def _remediation(vuln: dict[str, Any]) -> str:
    """Extract remediation guidance if available."""
    if vuln.get("database_specific", {}).get("fixed_in"):
        fixed = vuln["database_specific"]["fixed_in"]
        if fixed:
            return f"Upgrade to one of: {', '.join(fixed)}"
    return "Check references for upgrade or mitigation guidance."


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of integers for ordering."""
    if not version or not isinstance(version, str):
        return (0,)
    # Strip trailing non-numeric suffix (e.g. 1.2.3a1 -> 1.2.3)
    s = version.strip()
    for i, c in enumerate(s):
        if c.isdigit() or c == ".":
            continue
        s = s[:i]
        break
    parts = s.split(".")
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out) if out else (0,)


def _version_gte(version_a: str, version_b: str) -> bool:
    """Return True if version_a >= version_b (for fixed check: scanned >= fixed means fixed)."""
    ta = _parse_version(version_a)
    tb = _parse_version(version_b)
    # Pad shorter tuple with zeros
    max_len = max(len(ta), len(tb))
    ta = ta + (0,) * (max_len - len(ta))
    tb = tb + (0,) * (max_len - len(tb))
    return ta >= tb


def _is_version_fixed(vuln: dict[str, Any], pkg_version: str) -> bool:
    """
    Return True if the scanned package version is >= a 'fixed' version in OSV affected ranges.
    OSV affected[].ranges[].events can have {"fixed": "1.2.3"}. If pkg_version >= that, the vuln is fixed.
    """
    if not pkg_version or pkg_version == "-":
        return False
    affected = vuln.get("affected") or []
    for aff in affected:
        if not isinstance(aff, dict):
            continue
        ranges_list = aff.get("ranges") or []
        for rng in ranges_list:
            if not isinstance(rng, dict):
                continue
            events = rng.get("events") or []
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                fixed_ver = ev.get("fixed")
                if fixed_ver and isinstance(fixed_ver, str) and _version_gte(pkg_version, fixed_ver):
                    return True
    # database_specific.fixed_in (e.g. PyPI)
    fixed_in = vuln.get("database_specific") or {}
    fixed_list = fixed_in.get("fixed_in") or []
    if isinstance(fixed_list, list):
        for f in fixed_list:
            if isinstance(f, str) and _version_gte(pkg_version, f):
                return True
    elif isinstance(fixed_list, str) and _version_gte(pkg_version, fixed_list):
        return True
    return False


def _vuln_status(vuln: dict[str, Any], pkg_version: str) -> str:
    """
    Compute human-readable status from OSV vulnerability fields.
    - Withdrawn: advisory was withdrawn (withdrawn field present).
    - Fixed: scanned package version is >= a fixed version in OSV (optional).
    - Active: published and not withdrawn (and not fixed).
    - Unknown: no usable fields.
    """
    if vuln.get("withdrawn"):
        return "Withdrawn"
    if pkg_version and pkg_version != "-" and _is_version_fixed(vuln, pkg_version):
        return "Fixed"
    if vuln.get("published"):
        return "Active"
    # Present in OSV response but no published date → treat as Active (known finding)
    if vuln.get("id") or vuln.get("aliases"):
        return "Active"
    return "Unknown"


def _severity_label(vuln: dict[str, Any]) -> str:
    """
    Normalize OSV severity to a display label: Critical, High, Medium, Low, or empty.
    OSV may provide severity as top-level array (e.g. CVSS score) or in database_specific.
    Used only for HTML report presentation; color is not the only signal (we also show text).
    """
    # Top-level severity array: e.g. [{"type": "CVSS_V3", "score": "9.8"}]
    for sev in vuln.get("severity") or []:
        if isinstance(sev, dict):
            score_str = sev.get("score") or ""
            try:
                score = float(score_str)
                if score >= 9.0:
                    return "Critical"
                if score >= 7.0:
                    return "High"
                if score >= 4.0:
                    return "Medium"
                if score > 0:
                    return "Low"
            except (TypeError, ValueError):
                pass
    # database_specific.severity (string)
    ds = vuln.get("database_specific") or {}
    raw = (ds.get("severity") or "").upper()
    if "CRITICAL" in raw:
        return "Critical"
    if "HIGH" in raw:
        return "High"
    if "MEDIUM" in raw or "MODERATE" in raw:
        return "Medium"
    if "LOW" in raw:
        return "Low"
    return ""


def _enrich_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build enriched result list (ids, refs, remediation, severity, short summary, details_html, etc.) for HTML and JSON."""
    enriched = []
    for r in results:
        vulns = r.get("vulns") or []
        enriched_vulns = []
        pkg_version = r.get("version") or "-"
        for v in vulns:
            refs = _vuln_refs(v)
            summary = v.get("summary") or ""
            details_raw = v.get("details") or ""
            short = _short_summary(summary or details_raw)
            severity_label = _severity_label(v)
            rem_extra = enrich_vuln_remediation(v, pkg_version, severity_label)
            enriched_vulns.append({
                "id": v.get("id"),
                "ids": _vuln_ids(v),
                "summary": summary,
                "short_summary": short,
                "details": details_raw[:2000],
                "details_html": _markdown_headers_to_html(details_raw[:4000]),
                "references": refs,
                "ref_count": len(refs),
                "read_more_url": refs[0] if refs else "",
                "remediation": _remediation(v),
                "severity": severity_label,
                "published": v.get("published"),
                "withdrawn": v.get("withdrawn"),
                "affected": v.get("affected"),
                "database_specific": v.get("database_specific"),
                **rem_extra,
            })
        enriched.append({
            "name": r.get("name", "?"),
            "version": r.get("version") or "-",
            "vuln_count": len(vulns),
            "vulns": enriched_vulns,
        })
    return enriched


def _overview_rows(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build flat list of { package, vuln_id, severity, status, priority } for the overview table.
    Status is derived from OSV: Withdrawn, Fixed, Active, or Unknown."""
    rows = []
    for r in enriched:
        pkg_version = r.get("version") or "-"
        for v in r.get("vulns") or []:
            ids = v.get("ids") or ([v.get("id")] if v.get("id") else [])
            vuln_id = ids[0] if ids else "—"
            rows.append({
                "package": r.get("name", "?"),
                "version": pkg_version,
                "vuln_id": vuln_id,
                "severity": v.get("severity") or "Unknown",
                "status": _vuln_status(v, pkg_version),
                "priority": v.get("priority") or "",
            })
    return rows


def _severity_distribution(overview_rows: list[dict[str, Any]]) -> dict[str, int]:
    """Return counts by severity (Critical, High, Medium, Low, Unknown) for dashboard charts."""
    dist: dict[str, int] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
    for row in overview_rows:
        sev = (row.get("severity") or "Unknown").strip()
        key = sev if sev in dist else "Unknown"
        dist[key] = dist.get(key, 0) + 1
    return dist


def _fixable_counts(enriched: list[dict[str, Any]]) -> tuple[int, int]:
    """Return (fixable_count, non_fixable_count) from enriched results."""
    fixable = 0
    non_fixable = 0
    for r in enriched:
        for v in r.get("vulns") or []:
            if v.get("fix_available") is True:
                fixable += 1
            else:
                non_fixable += 1
    return fixable, non_fixable


def report_terminal(results: list[dict[str, Any]], console: Console | None = None) -> None:
    """
    Print scan results to the terminal using Rich.
    Each result: { "name", "version", "vulns": [...] }
    """
    out = console or Console()
    total_vulns = sum(len(r.get("vulns") or []) for r in results)
    out.print(f"\n[bold]Dependency scan complete.[/bold] Total vulnerabilities: [bold]{total_vulns}[/bold]\n")

    for r in results:
        name = r.get("name", "?")
        version = r.get("version") or "(no version)"
        vulns = r.get("vulns") or []
        if not vulns:
            out.print(f"  [green]OK[/green] {name} {version} - no known vulnerabilities")
            continue
        out.print(f"  [red]!![/red] [bold]{name}[/bold] {version} - {len(vulns)} vulnerability(ies)")
        for v in vulns:
            ids = _vuln_ids(v)
            summary = (v.get("summary") or v.get("details") or "")[:80]
            if summary and len((v.get("summary") or v.get("details") or "")) > 80:
                summary += "..."
            out.print(f"      [dim]IDs:[/dim] {', '.join(ids) or 'N/A'}")
            if summary:
                out.print(f"      [dim]{summary}[/dim]")
            rem = _remediation(v)
            out.print(f"      [dim]Remediation:[/dim] {rem}")
        out.print()

    if total_vulns > 0:
        table = Table(title="Summary by package")
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="white")
        table.add_column("Count", justify="right", style="red")
        table.add_column("CVE/OSV IDs", style="dim")
        for r in results:
            vulns = r.get("vulns") or []
            if not vulns:
                continue
            ids = []
            for v in vulns:
                ids.extend(_vuln_ids(v))
            table.add_row(
                r.get("name", "?"),
                r.get("version") or "-",
                str(len(vulns)),
                ", ".join(ids[:5]) + ("..." if len(ids) > 5 else ""),
            )
        out.print(table)


def report_html(
    results: list[dict[str, Any]],
    output_path: Path,
    template_dir: Path | None = None,
    *,
    generated_at: datetime | None = None,
    scanner_version: str | None = None,
    report_author: str | None = None,
    include_guidance: bool = False,
    input_label: str | None = None,
    ecosystem: str | None = None,
) -> None:
    """Render an HTML report using the Jinja2 template."""
    if template_dir is None:
        base = Path(__file__).resolve().parent
        template_dir = base / "templates"
        if not template_dir.exists():
            template_dir = base.parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.jinja")

    enriched = _enrich_results(results)
    total = sum(e["vuln_count"] for e in enriched)
    vulnerable_count = sum(1 for e in enriched if e["vuln_count"] > 0)
    overview_rows = _overview_rows(enriched)
    severity_distribution = _severity_distribution(overview_rows)
    fixable_count, non_fixable_count = _fixable_counts(enriched)
    improvement_recommendations = get_improvement_recommendations() if include_guidance else []

    now = generated_at or datetime.now(timezone.utc)
    version = scanner_version or SCANNER_VERSION
    author = report_author or DEFAULT_REPORT_AUTHOR

    html = template.render(
        total_vulnerabilities=total,
        package_count=len(results),
        vulnerable_package_count=vulnerable_count,
        results=enriched,
        overview_rows=overview_rows,
        severity_distribution=severity_distribution,
        fixable_count=fixable_count,
        non_fixable_count=non_fixable_count,
        improvement_recommendations=improvement_recommendations,
        include_guidance=include_guidance,
        input_label=input_label or "",
        ecosystem=ecosystem or "",
        generated_at=now,
        generated_at_year=now.strftime("%Y"),
        scanner_version=version,
        report_author=author,
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def report_json(
    results: list[dict[str, Any]],
    output_path: Path,
    *,
    generated_at: datetime | None = None,
    scanner_version: str | None = None,
    report_author: str | None = None,
    include_guidance: bool = False,
    input_label: str | None = None,
    ecosystem: str | None = None,
) -> None:
    """Write a machine-readable JSON report for CI/CD and compliance pipelines."""
    enriched = _enrich_results(results)
    total = sum(e["vuln_count"] for e in enriched)
    vulnerable_count = sum(1 for e in enriched if e["vuln_count"] > 0)
    fixable_count, non_fixable_count = _fixable_counts(enriched)

    now = generated_at or datetime.now(timezone.utc)
    version = scanner_version or SCANNER_VERSION
    author = report_author or DEFAULT_REPORT_AUTHOR

    report_meta: dict[str, Any] = {
        "generated_at": now.isoformat(),
        "scanner_version": version,
        "report_author": author,
        "package_count": len(results),
        "vulnerable_package_count": vulnerable_count,
        "total_vulnerabilities": total,
        "fixable_count": fixable_count,
        "non_fixable_count": non_fixable_count,
    }
    if input_label:
        report_meta["input_file"] = input_label
    if ecosystem:
        report_meta["ecosystem"] = ecosystem
    if include_guidance:
        report_meta["improvement_recommendations"] = get_improvement_recommendations()

    payload = {
        "report": report_meta,
        "remediation_guidance": {
            "remediation_summary": "This section provides actionable remediation guidance for vulnerabilities detected in the dependency analysis. The purpose is not only to identify known vulnerabilities, but to support informed, auditable decision-making in accordance with secure software development and supply chain risk management practices.",
            "evaluated_for_each_vuln": [
                "Fix availability (patched or non-patched)",
                "Recommended remediation action",
                "Remediation priority, based on severity and exploitability",
                "Potential impact of remediation, including compatibility or breaking-change risk",
            ],
            "recommended_actions": [
                "Upgrade dependency — A fixed version is available and upgrading is the preferred mitigation.",
                "Replace dependency — The dependency is unmaintained, end-of-life, or presents systemic risk.",
                "Remove dependency — The dependency is unused or non-essential and can be safely eliminated.",
                "Apply workaround / mitigation — No official fix exists; compensating controls or configuration changes are recommended.",
                "Monitor and document risk acceptance — No fix is currently available and removal is not feasible. Risk should be documented and periodically reviewed.",
            ],
            "priority_levels": {
                "Immediate": "Critical or High severity with known exploits or high exposure.",
                "Planned": "Medium severity or fix available with moderate effort.",
                "Monitor": "Low severity, no active exploit, or no fix available.",
            },
            "audit_considerations": "Chifleton remediation guidance is designed to be deterministic and reproducible, traceable to public vulnerability databases (e.g., OSV.dev), and suitable for inclusion in audit reports, SBOM reviews, and compliance documentation. Final remediation decisions remain the responsibility of the project maintainer or organization and should be documented as part of the secure development lifecycle.",
        },
        "packages": [
            {
                "name": e["name"],
                "version": e["version"],
                "vuln_count": e["vuln_count"],
                "vulns": [
                    {
                        "id": v.get("id"),
                        "ids": v.get("ids", []),
                        "summary": v.get("summary", ""),
                        "references": v.get("references", []),
                        "remediation": v.get("remediation", ""),
                        "severity": v.get("severity", ""),
                        "status": _vuln_status(v, e.get("version") or "-"),
                        "fix_available": v.get("fix_available"),
                        "recommended_action": v.get("recommended_action", ""),
                        "priority": v.get("priority", ""),
                        "remediation_risk": v.get("remediation_risk", ""),
                    }
                    for v in e["vulns"]
                ],
            }
            for e in enriched
        ],
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
