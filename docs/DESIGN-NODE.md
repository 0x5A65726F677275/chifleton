# Design: Node.js / JavaScript Ecosystem Support

This document describes the extension of Chifleton to support the JavaScript/Node.js ecosystem (npm, Vue.js, Next.js, and general JS/TS projects) while preserving evidence-ready reporting and U.S. software supply chain security policy alignment. It is intended for implementers, auditors, and security reviewers.

---

## 1. Dependency Detection

### 1.1 Target files

| File | Role | Authoritative for resolution? |
|------|------|------------------------------|
| **package.json** | Declares direct dependencies (and optionally dev/peer). Versions may be ranges (e.g. `^1.2.0`, `~2.0.0`). | **No.** Ranges do not pin exact versions; different installs can resolve to different versions. |
| **package-lock.json** | npm’s lockfile: exact resolved versions for the dependency tree. | **Yes (npm).** Authoritative for what `npm install` would install. |
| **yarn.lock** | Yarn’s lockfile: exact resolved versions. | **Yes (Yarn).** Authoritative when using Yarn. |
| **pnpm-lock.yaml** | pnpm’s lockfile: exact resolved versions. | **Yes (pnpm).** Authoritative when using pnpm. |

**Recommendation:** Prefer lockfiles when present. If only `package.json` exists, parse direct dependencies and resolve versions from ranges where possible (e.g. use a resolver or document “declared only, not resolved”). For evidence and reproducibility, **lockfile-based scanning is strongly preferred** and should be the default when a lockfile is found in the same directory as `package.json`.

### 1.2 Which file to use (priority)

1. If path is a directory: look for `package-lock.json`, then `yarn.lock`, then `pnpm-lock.yaml`. Use the first found.
2. If path is a file: use that file (`package.json`, `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml`).
3. For `chifleton scan .` or `chifleton scan . --ecosystem node`: same discovery in current directory.

**Why lockfiles are authoritative:** They record the exact dependency graph and versions that were installed. This matches what is actually in `node_modules` and what OSV can be queried against (exact version). EO 14028 and NIST SSDF emphasize knowing what you ship; lockfiles provide that evidence.

---

## 2. Vulnerability Scanning

### 2.1 OSV.dev integration

- Use the **same OSV API** as the Python scanner: `POST https://api.osv.dev/v1/query`.
- **Ecosystem identifier:** For npm packages use `ecosystem: "npm"`. This is the only change from the Python flow (which uses `ecosystem: "PyPI"`).
- **Query shape:** `{"package": {"name": "<pkg>", "ecosystem": "npm"}, "version": "<exact version>"}`. Version should be the exact resolved version from the lockfile (or the single version from package.json if no lockfile).
- **Transitive dependencies:** All three lockfiles list the full tree. Parse and query every package+version that appears in the tree (direct and transitive). Do not limit to top-level dependencies; transitives are part of what you ship and must be included for compliance.

### 2.2 Ecosystem identifiers (Python vs npm)

| Aspect | Python (PyPI) | Node (npm) |
|--------|----------------|-------------|
| OSV `ecosystem` | `PyPI` | `npm` |
| Package name | Case-normalized (e.g. Jinja2 → jinja2 in some contexts) | Case-sensitive; use name as in lockfile |
| Version format | PEP 440 (e.g. 1.2.3, 2.0.0a1) | SemVer (e.g. 1.2.3, 1.2.3-beta.0) |
| Lockfile | Optional (requirements.txt, pip freeze) | Expected (package-lock.json, yarn.lock, pnpm-lock.yaml) |

OSV accepts both ecosystems with the same API; the scanner must pass the correct `ecosystem` and the exact `version` string returned by the package manager.

### 2.3 Batch queries (optional optimization)

OSV provides `POST /v1/querybatch` for multiple packages in one request. For large lockfiles, using querybatch can reduce round-trips. The current Python path uses single-query; the Node scanner can start with single-query for simplicity and add querybatch as a follow-up optimization.

---

## 3. Architecture Design

### 3.1 Goals

- **Backward compatibility:** Existing `chifleton scan requirements.txt` and Python behavior unchanged.
- **Modularity:** Python and Node are separate “backends” (parsers + ecosystem identifier); shared core for OSV client, cache, reporting, CLI.
- **Extensibility:** Future ecosystems (Maven, Go, Rust) plug in as additional backends without rewriting core logic.

### 3.2 Proposed directory structure

```
scanner/
  __init__.py
  __main__.py
  cli.py              # Dispatcher: detect path/ecosystem, call correct backend
  cache.py            # Extend: cache key = (ecosystem, pkg, version)
  osv_client.py       # Extend: query(ecosystem, pkg, version) or keep per-ecosystem wrapper
  reporter.py         # Unchanged schema; add optional 'ecosystem' in JSON/HTML
  utils.py
  templates/
    report.html.jinja # Optional: show ecosystem per package or in summary

  # Parsers (per ecosystem)
  parsers/
    __init__.py       # Expose parse(path) -> list[ParsedDependency], detect ecosystem
    base.py           # ParsedDependency(name, version, ecosystem?)
    python.py         # requirements.txt, pyproject.toml, freeze (existing logic moved)
    node.py           # package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
    # future: maven.py, go.py, rust.py
```

**Alternative (flatter):** Keep `parser.py` for Python and add `parser_node.py`; `cli.py` chooses parser by file extension or `--ecosystem`. Both are valid; the parsers/ package scales better for many ecosystems.

### 3.3 Data flow

1. **CLI** receives `path` (file or directory) and optional `--ecosystem`.
2. **Detection:** If path is a directory, look for known files (requirements.txt, package.json, package-lock.json, etc.). If path is a file, infer ecosystem from filename. `--ecosystem node` forces Node handling.
3. **Parser** (Python or Node) returns a list of `(name, version)` or `(name, version, ecosystem)`.
4. **OSV client** is called per (ecosystem, name, version); cache key includes ecosystem.
5. **Reporter** receives the same result shape as today: list of `{name, version, vulns}`; optionally add `ecosystem` to each item for HTML/JSON.
6. **HTML/JSON** remain evidence-ready; only addition is optional `ecosystem` field and “Data source” can state “OSV (PyPI and npm)”.

### 3.4 Cache schema change

Current cache: `(pkg, version) -> response`. For multi-ecosystem, use `(ecosystem, pkg, version)` as the primary key so PyPI and npm entries do not collide (e.g. a package named “request” in PyPI vs “request” in npm). Migration: add an `ecosystem` column; default existing rows to `PyPI` or backfill when opening the DB.

---

## 4. CLI UX

### 4.1 Commands (backward compatible)

| Command | Behavior |
|---------|----------|
| `chifleton scan` | Current behavior: default to `requirements.txt` in cwd (Python). |
| `chifleton scan requirements.txt` | Current: Python scan. |
| `chifleton scan package.json` | **New:** Node scan (parse package.json; if sibling package-lock.json exists, use it; otherwise declare-only with a warning). |
| `chifleton scan package-lock.json` | **New:** Node scan from lockfile. |
| `chifleton scan .` | **New:** Detect ecosystem: if `package.json` or lockfile present, treat as Node; else if `requirements.txt` or `pyproject.toml` present, Python. If both, prefer Node when `--ecosystem node`, else prefer Python (or document: “both” could be a future option). |
| `chifleton scan . --ecosystem node` | **New:** Force Node detection in current directory (ignore Python files). |
| `chifleton scan . --ecosystem python` | **New:** Force Python detection. |

Existing flags (`--report`, `--no-cache`, `--fail-on-vuln`) apply unchanged. No breaking changes to existing invocations.

### 4.2 Ecosystem detection (for `scan .`)

1. If `--ecosystem` is set, use it (python | node).
2. Else list directory: if `package-lock.json` or `yarn.lock` or `pnpm-lock.yaml` or `package.json` exists → node. Else if `requirements.txt` or `pyproject.toml` exists → python.
3. If multiple ecosystems’ files exist and no `--ecosystem`, choose one by documented rule (e.g. Node first if both) or run one and warn “other ecosystem files present; use --ecosystem to scan them.”

---

## 5. Reporting

### 5.1 Schema (unchanged + optional ecosystem)

Current result item: `{ "name": str, "version": str, "vulns": [ ... ] }`. Add optional `"ecosystem": "npm" | "PyPI"` so reports can distinguish. Existing Python-only reports need not set it (or default to `PyPI`).

### 5.2 JSON report (machine-readable, evidence-ready)

Include for each package:

- `package` (or keep `name`): package name.
- `version`: resolved or declared version.
- `ecosystem`: `"PyPI"` or `"npm"` (optional for backward compat).
- `vulns`: array of vulnerabilities; each with:
  - `id` / `aliases`: CVE, OSV ID, etc.
  - `severity`: from OSV (CVSS or database_specific).
  - `summary` / `details`: description.
  - `references`: URLs.
  - `remediation` / `fixed_in`: fix availability (e.g. “Upgrade to 2.1.0” or “Check references”).

Top-level `report` object can add `ecosystems: ["PyPI", "npm"]` when multiple are present, and keep `generated_at`, `scanner_version`, `package_count`, `total_vulnerabilities` as today.

### 5.3 HTML report (auditor-friendly)

- Same layout as today: Summary Dashboard, Filters, Vulnerability Details table, Severity chart, Package Summary, Data Source & Metadata.
- In the Vulnerability Details table and Package Summary, add an optional column “Ecosystem” (PyPI / npm) when the report contains more than one ecosystem or when ecosystem is always npm (so auditors know the source).
- “Data Source & Metadata” section: state “OSV (PyPI and npm)” when both are used; otherwise “OSV (PyPI)” or “OSV (npm)”.
- No change to CVE/OSV IDs, severity, remediation, or fix availability presentation.

---

## 6. Policy Mapping (Node.js support)

The following text is suitable for inclusion in **ASSESSMENT.md** (e.g. a new subsection “Node.js / npm support” under scope and policy alignment).

### 6.1 Executive Order 14028

- **Knowing and documenting dependencies:** Node support extends “know what you ship” to npm dependencies. Lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml) provide the authoritative list of resolved packages and versions, analogous to pip freeze for Python. Scanning lockfiles and reporting vulnerabilities (with CVE/OSV IDs and remediation) supports EO 14028’s emphasis on dependency and supply chain transparency.
- **Transparent tooling:** The same open data source (OSV) is used for npm; no additional proprietary feeds. Architecture remains documented and auditable.

### 6.2 NIST SSDF (SP 800-218)

- **PW.4 (Produce well-secured software), RV.1 (Identify vulnerabilities), RV.2 (Analyze and determine risk):** Identifying known vulnerabilities in npm dependencies (direct and transitive) and reporting them with severity and fix availability supports PW.4 and the Respond to Vulnerabilities (RV) practices. Evidence-ready HTML and JSON reports provide verifiable artifacts for vulnerability management and risk decisions.
- **Documentation and verifiability:** Reports continue to include package name, version, ecosystem, CVE/OSV IDs, severity, and remediation; auditors can verify what was scanned and what was found.

### 6.3 CISA supply chain visibility

- **Dependency and vulnerability visibility:** Extending scanning to Node.js (including Vue.js, Next.js, and general JS/TS projects that use npm/yarn/pnpm) reduces blind spots in projects that ship both Python and JavaScript or that are purely Node-based. CISA guidance on knowing dependencies and using open, transparent tooling is met by the same OSV-based, open-source approach applied to npm.

### 6.4 Policy-to-feature mapping (Node)

| Policy / guidance | Relevant clause or goal | Node scanner feature |
|-------------------|-------------------------|------------------------|
| **EO 14028** | Sec. 4(c) – SBOM/equivalent; secure development | Dependency list from package-lock.json (or yarn/pnpm); vulnerability check against OSV; evidence-ready HTML/JSON. |
| **NIST SSDF** | PW.4, RV.1, RV.2 – identify/analyze vulnerabilities | Scan npm packages (including transitive); report CVE/OSV IDs, severity, remediation, fix availability. |
| **CISA** | Dependency and vulnerability visibility | Scan npm ecosystem; same reporting and transparency as Python path. |

---

## 7. Implementation Sketch

### 7.1 Parsing package-lock.json

```python
# scanner/parsers/node.py (sketch)

import json
from pathlib import Path
from typing import Any

def parse_package_lock(path: Path) -> list[tuple[str, str]]:
    """
    Parse package-lock.json and return (name, version) for all packages
    in the lockfile (dependencies + optionalDependencies; dev optional).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    deps: list[tuple[str, str]] = []
    packages = data.get("packages") or {}
    # npm v7+ lockfile: "node_modules/pkg" -> { "version": "1.2.3" }
    for key, pkg in packages.items():
        if key == "":  # root project
            continue
        if not isinstance(pkg, dict):
            continue
        version = pkg.get("version")
        if not version:
            continue
        # key is "node_modules/foo" or "node_modules/foo/bar"
        name = key.replace("node_modules/", "").split("/")[0]
        deps.append((name, version))
    return list(dict.fromkeys(deps))  # dedupe by (name, version)
```

Note: npm v6 and earlier use a different lockfile shape (`dependencies` tree). A production implementation should support both or document “npm lockfile v7+” and add a separate branch for v6 format.

### 7.2 Querying OSV for npm packages

```python
# scanner/osv_client.py (extend)

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
ECOSYSTEM_PYPI = "PyPI"
ECOSYSTEM_NPM = "npm"
TIMEOUT = 30

def query_vulnerabilities(
    pkg: str,
    version: str | None,
    ecosystem: str = ECOSYSTEM_PYPI,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "package": {"name": pkg, "ecosystem": ecosystem},
    }
    if version:
        payload["version"] = version
    try:
        resp = requests.post(OSV_QUERY_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except requests.RequestException as e:
        return {"_error": str(e), "vulns": []}
```

Existing callers pass no ecosystem and default to PyPI; Node backend passes `ecosystem=ECOSYSTEM_NPM`.

### 7.3 Normalizing results into existing report schema

The reporter already expects `results: list[dict]` with `{ "name", "version", "vulns" }`. The Node backend can produce the same structure; only the source of the list changes (Node parser + OSV with ecosystem=npm). Optional: add `"ecosystem": "npm"` to each result dict so the JSON report and HTML can show it. No change to `_enrich_results`, `_overview_rows`, or `report_html`/`report_json` beyond optionally reading `ecosystem` for display.

```python
# In CLI (sketch), after obtaining deps from Node parser:
results = []
for name, version in node_deps:
    raw = query_vulnerabilities(name, version, ecosystem=ECOSYSTEM_NPM)
    vulns = get_vulns_from_response(raw)
    results.append({"name": name, "version": version, "vulns": vulns})
# Then same as Python path:
report_terminal(results, console)
report_html(results, out_path, **meta)
report_json(results, out_path, **meta)
```

---

## 8. Risks and Limitations

### 8.1 Lockfile accuracy

- **Risk:** Lockfiles can be out of date (e.g. `package-lock.json` not regenerated after a manual edit to `package.json`). Scanning the lockfile then reports what the lockfile says, not necessarily what is in `node_modules`.
- **Mitigation:** Document in user docs and report metadata: “This report is based on [package-lock.json]. Ensure the lockfile is committed and up to date. Run `npm install` (or equivalent) before scanning to refresh the lockfile.” Optionally add a note in the HTML report: “Input: package-lock.json (resolved tree).”

### 8.2 Private packages / missing from OSV

- **Risk:** Private or internal packages are not in the public npm registry or OSV. They will not be found by OSV and may appear as “no known vulnerabilities” rather than “not in database.”
- **Mitigation:** Document that only public npm packages are covered. Optionally list in the report any package names that returned no OSV result so auditors can distinguish “no vulns” from “not in OSV.” Do not claim coverage of private registries unless explicitly supported later.

### 8.3 Multiple lockfiles in one repo

- **Risk:** Monorepos may have multiple `package.json`/lockfile pairs. Scanning a single directory may only scan one of them.
- **Mitigation:** Document that `scan .` targets one directory. Future work could support `--all` or a list of paths to scan multiple roots and merge results into one report with clear labels (e.g. project path per section).

### 8.4 Yarn / pnpm lockfile format

- **Risk:** yarn.lock and pnpm-lock.yaml have different formats than package-lock.json. Parsing them requires separate logic and testing.
- **Mitigation:** Implement and test each format; document supported lockfile versions. If a format is not supported, fail with a clear message (“yarn.lock format v2 not yet supported”) rather than misparsing.

### 8.5 Audit suitability

- For audits, recommend: (1) use lockfile-based scan, (2) run in CI after `npm ci` / `yarn install --frozen-lockfile` so the lockfile is the source of truth, (3) retain the generated HTML/JSON as evidence with timestamp and scanner version (already in Data Source & Metadata).

---

## 9. Summary and next steps

- **Dependency detection:** Prefer lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml); support package.json with a “declared only” caveat when no lockfile.
- **Vulnerability scanning:** Same OSV API with `ecosystem: "npm"`; include transitive dependencies.
- **Architecture:** Modular parsers (Python vs Node); shared OSV client (with ecosystem parameter), cache (keyed by ecosystem), and reporter; optional `ecosystem` in reports.
- **CLI:** Backward compatible; add `scan package.json`, `scan .`, and `--ecosystem node|python`.
- **Reporting:** Same evidence-ready HTML/JSON; add ecosystem where useful; policy mapping (EO 14028, NIST SSDF, CISA) documented for Node support.
- **Risks:** Lockfile freshness, private packages, multiple roots, lockfile format support; document and mitigate for auditors.

This document can be used to create GitHub issues (e.g. one per section or per task: parser node, cache ecosystem, CLI detection, report ecosystem field, docs, ASSESSMENT update) and to update ASSESSMENT.md with the Node.js policy mapping and scope.
