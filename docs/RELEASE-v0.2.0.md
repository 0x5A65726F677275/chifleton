# Release notes for v0.2.0

Use the content below when creating the GitHub Release for tag **v0.2.0**.

---

## Release title
**v0.2.0: Remediation Guidance, ASSESSMENT Chapter, and Design Docs**

## Description (paste into GitHub Release)

### What's New

- **Remediation Guidance** — HTML report includes a dedicated "Remediation Guidance" section (recommended actions, priority levels, audit considerations). JSON report adds top-level `remediation_guidance` for compliance and automation.
- **ASSESSMENT.md** — New chapter "Remediation & Secure Usage" (purpose, remediation approach, secure usage guidelines, policy alignment, evidence-ready design).
- **Node.js design** — Design doc and issue checklist for future npm/Node support: `docs/DESIGN-NODE.md`, `docs/ASSESSMENT-NODE-UPDATE.md`, `docs/GITHUB-ISSUES-NODE.md`.
- **`python3 -m chifleton scan`** — Runnable as a module; `chifleton` package with `__main__.py`.
- **`--from-freeze`** — Scan pip-freeze style input (stdin or file) for installed package versions.
- **`--fail-on-vuln`** — Exit code 1 when any vulnerability is found (CI use).
- **Sample fixtures** — `tests/fixtures/package.json` and `package-lock.json` for future Node scanner testing.

### Improvements

- Report metadata de-duplicated: single "Data Source & Metadata" section; header shows only generated date.
- Filters section and nav order aligned with page order (Overview → Filters → Vulnerability Details → …).
- README: example commands, Linux/WSL (venv/pipx) and externally-managed-environment notes, default `--report` (html+json) clarified.

### Notes

- No breaking changes.
- All existing vulnerability data and report structure preserved.
- Reports remain timestamped and reproducible.

### Assets

Attach **Source code (zip)** and **Source code (tar.gz)** from the tag when publishing the release.
