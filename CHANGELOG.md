# Changelog

All notable changes to Chifleton are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.1] - 2026-02-10

### Changed

- **Rebrand** — Project renamed from AuditDeps to **Chifleton**. CLI: `chifleton scan` (backward-compatible `auditdeps` script retained). Package: `chifleton` on PyPI. Cache directory: `~/.chifleton`.
- **Report UI** — Filters: order Package → Vulnerability ID → Severity → Status; Severity and Status are multi-select (checkboxes). Severity by package: top 6 + Others pie chart with legend scroll and tooltips. View details: expand inline below each row (one vulnerability per row); print/PDF auto-expands all rows. Pagination based on visible (filtered) row count. CISA-inspired colors (header #005288, accent #002b47).

## [0.2.0] - 2026-02-09

### Added

- **Remediation Guidance** — HTML report includes a dedicated "Remediation Guidance" section (recommended actions, priority levels, audit considerations). JSON report adds top-level `remediation_guidance` (remediation_summary, recommended_actions, priority_levels, audit_considerations).
- **ASSESSMENT.md** — New chapter "Remediation & Secure Usage" (purpose, remediation approach, secure usage guidelines, policy alignment, evidence-ready design). Section numbering updated (3–8).
- **Node.js design** — Design doc and issue checklist for future npm/Node support: `docs/DESIGN-NODE.md`, `docs/ASSESSMENT-NODE-UPDATE.md`, `docs/GITHUB-ISSUES-NODE.md`.
- **Sample fixtures** — `tests/fixtures/package.json` and `tests/fixtures/package-lock.json` for Node scanner testing (intentionally older/vulnerable versions).
- **`python3 -m chifleton scan`** — Runnable as a module; `chifleton` package with `__main__.py` added.
- **`--from-freeze`** — Scan pip-freeze style input (stdin or file) for installed package versions.
- **`--fail-on-vuln`** — Exit code 1 when any vulnerability is found (CI use).
- **README** — Example commands, Linux/WSL (venv/pipx) and externally-managed-environment notes, default `--report` (html+json) clarified.

### Changed

- Report metadata de-duplicated: single "Data Source & Metadata" section; header shows only generated date; Executive Summary and footer reference that section.
- Filters section and nav order aligned with page order (Overview → Filters → Vulnerability Details → …).

## [0.1.0] - Initial release

- Python dependency scan (requirements.txt, pyproject.toml, pip-freeze).
- OSV.dev integration; local SQLite cache.
- HTML and JSON reports; terminal output.
- EO 14028 / NIST SSDF / CISA alignment and ASSESSMENT.md.
