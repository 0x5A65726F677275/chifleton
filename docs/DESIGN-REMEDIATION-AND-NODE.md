# Design: Remediation Intelligence, Improvement Recommendations, and Node.js Support

This document extends Chifleton with **Node.js/JavaScript ecosystem support**, **remediation intelligence**, **improvement recommendations**, and **secure supply chain guidelines**. It is written for implementers, security auditors, and government contractors. Content is structured for direct use in code tasks, documentation, and compliance evidence (e.g. ASSESSMENT.md).

---

## 1. Multi-Ecosystem Dependency Detection

### 1.1 Target files (Node.js)

| File | Role | Authoritative for audits? |
|------|------|---------------------------|
| **package.json** | Declares direct (and optionally dev/peer) dependencies. Versions are often **ranges** (e.g. `^1.2.0`, `~2.0.0`). | **No.** Ranges do not pin exact versions; different installs can resolve to different versions. Use for "declared only" when no lockfile exists. |
| **package-lock.json** | npm lockfile: **exact resolved versions** for the full dependency tree. | **Yes (npm).** Authoritative for what `npm install` installs. |
| **yarn.lock** | Yarn lockfile: exact resolved versions. | **Yes (Yarn).** Authoritative when using Yarn. |
| **pnpm-lock.yaml** | pnpm lockfile: exact resolved versions. | **Yes (pnpm).** Authoritative when using pnpm. |

**Declared vs resolved:**

- **Declared:** What developers write in `package.json` (dependencies, devDependencies). Versions may be ranges; not sufficient alone for reproducible or audit-ready scans.
- **Resolved:** What the package manager actually installs, recorded in lockfiles. This is what should be treated as **authoritative for audits** because it matches what is in `node_modules` and what OSV can be queried against (exact version).

**Recommendation:** When a lockfile is present in the same directory as `package.json`, use the lockfile for the dependency list. If only `package.json` exists, parse direct dependencies and either resolve ranges (e.g. via a resolver) or report with a clear "declared only, not resolved" caveat. For evidence and EO 14028 alignment, **lockfile-based scanning is strongly preferred**.

### 1.2 Which file to use (priority)

1. **Explicit path:** If the user passes a file path, use that file (`package.json`, `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml`).
2. **Directory (e.g. `chifleton scan .`):** Look for `package-lock.json`, then `yarn.lock`, then `pnpm-lock.yaml` in that directory. Use the first found. If none, look for `package.json` and use it with a "declared only" warning.
3. **`--ecosystem node`:** Restrict discovery to Node files only; ignore Python files.
4. **`--ecosystem python`:** Restrict to `requirements.txt` / `pyproject.toml` (current behavior).

### 1.3 Monorepos and framework-specific setups

- **Monorepos:** Multiple `package.json` / lockfile pairs may exist (e.g. `apps/web`, `packages/shared`). A single `chifleton scan .` targets one directory. Document that users should run the scanner per package root or use multiple paths; future work may add `--all` or a manifest of paths.
- **Vue.js / Next.js / general JS/TS:** These use `package.json` and one of the three lockfiles. No special handling beyond using the lockfile when present; framework is transparent to the scanner.
- **Workspaces (npm/yarn/pnpm):** Root lockfile often contains the full workspace tree. Parsing the root lockfile is sufficient for "all packages in the workspace" when the lockfile format encodes the full tree.

---

## 2. Vulnerability Detection (Baseline)

- **API:** Same OSV API: `POST https://api.osv.dev/v1/query` (and optionally `POST /v1/querybatch` for many packages).
- **npm:** Use `ecosystem: "npm"` and exact `version` from the lockfile (or single version from package.json if no lockfile).
- **Transitive dependencies:** All lockfiles list the full tree. Parse and query every package+version (direct and transitive). Do not limit to top-level; transitives are part of what is shipped and must be included for compliance.
- **Normalized schema:** Python and Node results share the same report schema: each item is `{ "name", "version", "vulns": [...], optional "ecosystem" }`. OSV response fields (ids, severity, summary, references, affected ranges) are normalized in the reporter so HTML/JSON are ecosystem-agnostic.

---

## 3. Remediation Intelligence (Core New Requirement)

For each detected vulnerability, provide:

| Field | Description | Example |
|-------|-------------|--------|
| **recommended_action** | What to do: upgrade (exact or range), replace, remove, or apply patch/workaround. | `"Upgrade to >=4.17.21"` |
| **fix_available** | Boolean: whether a fix is known (e.g. fixed version in OSV or database_specific). | `true` |
| **remediation_risk** | Likelihood of breaking changes: Low / Medium / High / Unknown. | `"Low"` |
| **priority** | Triage: Immediate / Planned / Monitor. | `"Immediate"` |

**Example (JSON):**

```json
{
  "package": "lodash",
  "current_version": "4.17.19",
  "vulnerability_id": "OSV-2021-XYZ",
  "severity": "HIGH",
  "fix_available": true,
  "recommended_action": "Upgrade to >=4.17.21",
  "priority": "Immediate"
}
```

**Derivation rules:**

- **fix_available:** True if OSV `affected[].ranges[].events[].fixed` or `database_specific.fixed_in` lists at least one version; else false.
- **recommended_action:** If fixed_in/fixed versions exist, "Upgrade to &lt;version_or_range&gt;"; if advisory says replace/remove, use that; else "Check references for upgrade or mitigation."
- **remediation_risk:** Heuristic: major version bump (e.g. 1.x → 2.x) → Medium/High; patch/minor → Low; unknown → Unknown.
- **priority:** Critical → Immediate; High → Immediate; Medium → Planned; Low/Unknown → Monitor (configurable).

---

## 4. Improvement Recommendations (Project-Level)

Beyond per-vulnerability remediation, generate **project-level** guidance, e.g.:

- Enable lockfile enforcement (e.g. `npm ci`, fail if lockfile out of date).
- Reduce dependency sprawl (audit unused or duplicate packages).
- Remove unused or unmaintained packages.
- Prefer pinned versions over ranges where feasible.
- Introduce automated dependency updates (Dependabot, Renovate, or similar).
- Add SBOM generation to CI/CD.

**Classification:**

- **Security impact:** High / Medium / Low.
- **Effort:** Low / Medium / High.
- **Policy relevance:** EO 14028, NIST SSDF, CISA (short label for auditors).

Output: a list of recommendations with id, title, description, security_impact, effort, policy_relevance, and optional checklist item for the report.

---

## 5. Secure Supply Chain Guidelines (Human-Readable)

Produce a **developer-friendly, audit-ready** guideline section covering:

- What to do after running Chifleton (triage, remediate, document).
- How often to run scans (e.g. every PR, nightly, before release).
- How to document remediation decisions (tickets, comments, exception register).
- How to handle: no-fix vulnerabilities, legacy dependencies, business risk exceptions.

This content must be suitable for:

- **ASSESSMENT.md**
- Security review documents
- Internal SDLC policies

Text is provided as a separate fragment (e.g. `docs/SECURE-SUPPLY-CHAIN-GUIDELINES.md`) and optionally included in HTML/JSON when `--include-guidance` is set.

---

## 6. CLI and UX Enhancements

Proposed options (backward compatible):

| Command / option | Behavior |
|-----------------|----------|
| `chifleton scan package.json` | Node scan (use sibling lockfile if present; else declared-only with warning). |
| `chifleton scan .` | Auto-detect: Node if lockfile/package.json; else Python. |
| `chifleton scan . --ecosystem node` | Force Node; ignore Python files. |
| `chifleton scan . --ecosystem python` | Force Python. |
| `chifleton scan . --include-guidance` | Include remediation guidance and improvement checklist + secure guidelines section in HTML/JSON. |
| `chifleton scan . --fail-on critical` | Exit 1 if any vulnerability has severity Critical. |
| `chifleton scan . --fail-on high` | Exit 1 if any Critical or High. |

**Values for `--fail-on`:** `critical` | `high` | `medium` | `low` | `vuln` (any; same as current `--fail-on-vuln`).

**Backward compatibility:** Existing `chifleton scan`, `chifleton scan requirements.txt`, `--report`, `--no-cache`, `--from-freeze`, `--fail-on-vuln` remain unchanged. Detection and guidance output are clearly separated (guidance optional via `--include-guidance`).

---

## 7. Reporting (Evidence-Ready Extensions)

**Per-vulnerability:** Add to HTML and JSON:

- Remediation guidance (existing + new fields: fix_available, recommended_action, priority, remediation_risk).

**Summary tables:**

- **Fixable vs non-fixable:** Count of vulnerabilities where fix_available is true vs false.
- **High-risk dependencies:** Packages with at least one Critical or High finding.
- **Improvement checklist:** List of project-level recommendations (when `--include-guidance`).

**Metadata:** Timestamped, attributable output (author, scanner version, data source) — already present; extend with optional `input_file` and `ecosystem` in report header.

---

## 8. Policy and Compliance Mapping

Explicit mapping for ASSESSMENT.md and evidence packages:

| Area | Policy / guidance | Mapping |
|------|-------------------|--------|
| **Detection** | EO 14028 (visibility, transparency) | Dependency list from lockfile/requirements; known vulns from OSV; evidence-ready reports. |
| **Remediation** | NIST SSDF PW.4, RV.1, RV.2 | Remediation intelligence (recommended action, fix availability, priority) supports Respond to Vulnerabilities; reports document what was found and what to do. |
| **Improvement guidance** | CISA Secure Software practices | Project-level recommendations and secure supply chain guidelines align with CISA guidance on dependency management and SDLC. |

Use the same table (or expanded) in ASSESSMENT.md so reviewers can trace features to clauses.

---

## 9. Implementation Sketch

### 9.1 Parsing package-lock.json (npm v7+)

```python
# scanner/parsers/node.py (sketch)

import json
from pathlib import Path

def parse_package_lock(path: Path) -> list[tuple[str, str]]:
    """Return (name, version) for all packages in lockfile (deduped)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    deps: list[tuple[str, str]] = []
    packages = data.get("packages") or {}
    for key, pkg in packages.items():
        if key == "" or not isinstance(pkg, dict):
            continue
        version = pkg.get("version")
        if not version:
            continue
        name = key.replace("node_modules/", "").split("/")[0]
        deps.append((name, version))
    return list(dict.fromkeys(deps))
```

npm v6 and earlier use a different shape (`dependencies` tree); production code should support both or document "npm lockfile v7+".

### 9.2 Querying OSV for npm

```python
# scanner/osv_client.py

def query_vulnerabilities(
    pkg: str,
    version: str | None,
    ecosystem: str = "PyPI",
) -> dict[str, Any]:
    payload = {
        "package": {"name": pkg, "ecosystem": ecosystem},
    }
    if version:
        payload["version"] = version
    resp = requests.post(OSV_QUERY_URL, json=payload, timeout=TIMEOUT)
    # ... same as today, ecosystem in payload
```

### 9.3 Enriching vulnerability data with remediation hints

In reporter (or a dedicated `remediation.py`): for each vuln, compute fix_available from OSV `fixed_in` / `events[].fixed`; set recommended_action string; set priority from severity; set remediation_risk from version delta heuristic. Attach to each enriched vuln dict so HTML/JSON include them.

### 9.4 Unified report schema

Single schema for Python and Node: `packages[]` with `name`, `version`, `ecosystem` (optional), `vulns[]` with `id`, `ids`, `summary`, `references`, `remediation`, `severity`, `status`, plus `fix_available`, `recommended_action`, `priority`, `remediation_risk`. Report-level: `fixable_count`, `non_fixable_count`, `improvement_recommendations` (when guidance included).

---

## 10. Risks and Limitations

| Risk | Mitigation |
|------|------------|
| **Lockfile trust** | Lockfile may be stale. Document: "Ensure lockfile is committed and up to date; run npm install / npm ci before scanning." Report metadata can record input file name. |
| **Transitive complexity** | Large trees may yield many OSV calls and long reports. Use batch API where possible; consider rate limiting; document that full tree is intentional for compliance. |
| **False positives / incomplete fixes** | OSV data may be wrong or fix versions incomplete. Recommend users verify fixes in a test environment; document "Check references" for uncertain cases. |
| **Private packages** | Not in public npm or OSV. Document that only public packages are covered; optionally list packages with no OSV result so "no vulns" vs "not in DB" is clear. |
| **Multiple lockfiles in monorepo** | Scanning one directory may miss others. Document per-root scanning; future: multi-path or workspace manifest. |

All mitigations should be stated in user docs and, where appropriate, in the HTML report (e.g. "Limitations" in Data Source & Metadata) so audits accept the tool's scope and caveats.

---

*This design supports implementation tasks, ASSESSMENT.md updates, and compliance evidence. For Node-only detection and CLI behavior, see DESIGN-NODE.md.*
