"""CLI entry point for Chifleton."""

import sys
from pathlib import Path

import click
from rich.console import Console

from datetime import datetime, timezone

from scanner import __author__ as REPORT_AUTHOR, __version__ as SCANNER_VERSION
from scanner.cache import get_cached, init_cache, set_cached
from scanner.osv_client import get_vulns_from_response, query_vulnerabilities
from scanner.parser import parse_dependency_file, parse_freeze
from scanner.parsers.detect import get_dependencies, resolve_path_for_scan
from scanner.reporter import report_html, report_json, report_terminal, _severity_label
from scanner.utils import resolve_path

# For --fail-on: severity rank (higher = worse)
FAIL_ON_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "vuln": 0}


def _max_severity_rank(results: list[dict]) -> int:
    """Return the highest severity rank among all vulns in results (0 = none)."""
    from scanner.remediation import priority_from_severity  # noqa: avoid circular import
    rank = 0
    for r in results:
        for v in r.get("vulns") or []:
            sev = _severity_label(v)
            rk = FAIL_ON_SEVERITY_RANK.get((sev or "").lower(), 0)
            if rk > rank:
                rank = rk
    return rank


@click.group()
def cli() -> None:
    """Chifleton — dependency vulnerability scanner (OSV.dev)."""


@cli.command("scan")
@click.argument("path", required=False, type=str, default=None)
@click.option(
    "--report",
    "reports",
    type=click.Choice(["html", "json", "none"], case_sensitive=False),
    default=("html", "json"),
    multiple=True,
    help="Output format(s): 'html' writes scan-report.html; 'json' writes scan-report.json. Default: both. Use --report none for terminal-only.",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable SQLite cache; always query OSV API.",
)
@click.option(
    "--from-freeze",
    "from_freeze",
    is_flag=True,
    help="Read pip-freeze style input (name==version per line). Use path '-' or omit path to read from stdin.",
)
@click.option(
    "--fail-on-vuln",
    "fail_on_vuln",
    is_flag=True,
    help="Exit with code 1 if any vulnerability is found (for CI).",
)
@click.option(
    "--ecosystem",
    type=click.Choice(["python", "node"], case_sensitive=False),
    default=None,
    help="Force ecosystem: python (requirements.txt/pyproject.toml) or node (package.json, lockfiles). Default: auto-detect from path.",
)
@click.option(
    "--include-guidance",
    "include_guidance",
    is_flag=True,
    help="Include remediation guidance and improvement checklist in HTML/JSON reports.",
)
@click.option(
    "--fail-on",
    "fail_on_severity",
    type=click.Choice(["critical", "high", "medium", "low", "vuln"], case_sensitive=False),
    default=None,
    help="Exit with code 1 if any vulnerability has this severity or higher (e.g. --fail-on critical). 'vuln' = any vulnerability (same as --fail-on-vuln).",
)
def scan(
    path: str | None,
    reports: tuple[str, ...],
    no_cache: bool,
    from_freeze: bool,
    fail_on_vuln: bool,
    ecosystem: str | None,
    include_guidance: bool,
    fail_on_severity: str | None,
) -> None:
    """Scan a dependency file or directory for known vulnerabilities (Python or Node.js)."""
    console = Console()

    if from_freeze:
        if path is None or path == "-":
            try:
                content = sys.stdin.read()
            except OSError as e:
                console.print(f"[red]Error reading stdin:[/red] {e}")
                raise SystemExit(1)
            deps = parse_freeze(content)
            # Ensure ecosystem on ParsedDependency for cache/OSV
            from scanner.parser import ParsedDependency
            deps = [d._replace(ecosystem="PyPI") if getattr(d, "ecosystem", None) is None else d for d in deps]
            report_dir = Path.cwd()
            input_label = "stdin"
            ecosystem_osv = "PyPI"
            from_lockfile = True
        else:
            req_path = resolve_path(path)
            if not req_path.exists():
                console.print(f"[red]Error:[/red] File not found: {req_path}")
                raise SystemExit(1)
            try:
                content = req_path.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                console.print(f"[red]Error reading file:[/red] {e}")
                raise SystemExit(1)
            deps = parse_freeze(content)
            from scanner.parser import ParsedDependency
            deps = [d._replace(ecosystem="PyPI") if getattr(d, "ecosystem", None) is None else d for d in deps]
            report_dir = req_path.parent
            input_label = str(req_path)
            ecosystem_osv = "PyPI"
            from_lockfile = True
    else:
        resolved = resolve_path_for_scan(path)
        if not resolved.exists():
            console.print(f"[red]Error:[/red] Path not found: {resolved}")
            raise SystemExit(1)
        ecosystem_osv, deps, input_label, from_lockfile = get_dependencies(
            resolved,
            ecosystem_override=ecosystem,
        )
        if not deps:
            console.print("[yellow]No dependencies found in[/yellow]", input_label)
            if not from_lockfile and "package.json" in str(resolved):
                console.print("[dim]Tip: Use a lockfile (package-lock.json, yarn.lock, pnpm-lock.yaml) for resolved versions.[/dim]")
            return
        report_dir = Path(input_label).parent if Path(input_label).exists() else resolved

    if not no_cache:
        init_cache()

    results = []
    for dep in deps:
        eco = getattr(dep, "ecosystem", None) or ecosystem_osv
        cached = None if no_cache else get_cached(dep.name, dep.version, ecosystem=eco)
        if cached is not None:
            raw = cached
        else:
            raw = query_vulnerabilities(dep.name, dep.version, ecosystem=eco)
            if not no_cache and "_error" not in raw:
                set_cached(dep.name, dep.version, raw, ecosystem=eco)
        vulns = get_vulns_from_response(raw)
        if raw.get("_error"):
            console.print(f"[yellow]Warning:[/yellow] OSV request failed for {dep.name}: {raw['_error']}")
        results.append({
            "name": dep.name,
            "version": dep.version,
            "vulns": vulns,
        })

    report_terminal(results, console)

    generated_at = datetime.now(timezone.utc)
    meta = {
        "generated_at": generated_at,
        "scanner_version": SCANNER_VERSION,
        "report_author": REPORT_AUTHOR,
        "include_guidance": include_guidance,
        "input_label": input_label,
        "ecosystem": ecosystem_osv,
    }

    for report in reports or ():
        if report == "none":
            continue
        if report == "html":
            out_path = report_dir / "scan-report.html"
            report_html(results, out_path, **meta)
            console.print(f"[green]HTML report written to[/green] {out_path}")
        elif report == "json":
            out_path = report_dir / "scan-report.json"
            report_json(results, out_path, **meta)
            console.print(f"[green]JSON report written to[/green] {out_path}")

    total_vulns = sum(len(r["vulns"]) for r in results)
    if fail_on_vuln and total_vulns > 0:
        raise SystemExit(1)
    if fail_on_severity:
        required_rank = FAIL_ON_SEVERITY_RANK.get(fail_on_severity.lower(), 0)
        max_rank = _max_severity_rank(results)
        if max_rank >= required_rank and (required_rank > 0 or total_vulns > 0):
            raise SystemExit(1)


def main() -> None:
    """Entry point for console_script."""
    cli()


if __name__ == "__main__":
    main()
