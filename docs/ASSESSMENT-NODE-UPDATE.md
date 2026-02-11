# ASSESSMENT.md update: Node.js / npm support

Merge the following into **ASSESSMENT.md** when Node.js support is implemented (or in a “Planned” subsection if documenting roadmap).

---

## 1. Scope table (amend “In scope”)

**Current:**

| In scope | Out of scope (current version) |
|----------|--------------------------------|
| Python `requirements.txt` and `pyproject.toml` [project.dependencies] | Other ecosystems (npm, etc.) |

**Replace “Out of scope” row with:**

| In scope | Out of scope (current version) |
|----------|--------------------------------|
| Python: `requirements.txt`, `pyproject.toml` [project.dependencies], pip-freeze style | Other ecosystems (Maven, Go, Rust, etc.) unless added in a later release |
| Node/npm: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` (lockfile preferred for resolution) | Private npm registries; SBOM generation; integrity/signature checks |

(Keep remaining rows for single data source, CLI, reports, cache, evidence-ready design as-is.)

---

## 2. New subsection: Node.js / npm support (policy alignment)

Insert after **§ 2.4 Policy-to-feature mapping** (or in § 2 as 2.5).

### 2.5 Node.js / npm ecosystem

Support for the JavaScript/Node.js ecosystem (npm, including Vue.js, Next.js, and general JS/TS projects) extends the same evidence-ready model to lockfile-based dependency scanning.

**Executive Order 14028:** Knowing and documenting dependencies now includes npm dependencies. Lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml) provide the authoritative resolved dependency set. Scanning them and reporting CVE/OSV IDs and remediation supports supply chain transparency.

**NIST SSDF (SP 800-218), PW.4, RV.1, RV.2:** Identifying and analyzing vulnerabilities in npm packages (direct and transitive) and reporting severity and fix availability supports producing well-secured software and responding to vulnerabilities. HTML and JSON reports remain verifiable evidence for vulnerability management.

**CISA supply chain visibility:** Node support reduces dependency blind spots for projects that ship JavaScript/Node (including Vue and Next.js). The same open, OSV-based approach applies; no proprietary feeds.

**Policy-to-feature mapping (Node):**

| Policy / guidance | Relevant clause or goal | Node scanner feature |
|-------------------|-------------------------|------------------------|
| EO 14028 | Sec. 4(c) – SBOM/equivalent; secure development | Dependency list from lockfile; vulnerability check via OSV; evidence-ready HTML/JSON. |
| NIST SSDF | PW.4, RV.1, RV.2 | Scan npm (including transitive); report CVE/OSV IDs, severity, remediation, fix availability. |
| CISA | Dependency and vulnerability visibility | Scan npm; same reporting and transparency as Python. |

---

## 3. Evidence-ready features table (add row)

Add one row to the “Evidence-Ready Features” table:

| Feature | Description |
|--------|-------------|
| **Node/npm scanning** | Parses package-lock.json (or yarn.lock, pnpm-lock.yaml, package.json); queries OSV (ecosystem npm); reports include package, version, ecosystem, CVE/OSV IDs, severity, remediation; lockfile preferred for authoritative resolution. |

---

Use the above verbatim or adapt to the existing ASSESSMENT.md heading level and table style.
