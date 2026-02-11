# Risks and Limitations (Audit-Acceptable Mitigations)

This document describes known risks and limitations of Chifleton (including Node.js support and remediation guidance) and mitigation strategies suitable for security auditors and government reviewers.

---

## 1. Lockfile Trust and Freshness

**Risk:** The lockfile (package-lock.json, yarn.lock, pnpm-lock.yaml) may be out of date. For example, someone may have edited package.json without regenerating the lockfile. The scan then reports on what the lockfile says, not necessarily what is in node_modules or what would be installed in CI.

**Mitigation:**

- Document in user docs and report metadata: "This report is based on [filename]. Ensure the lockfile is committed and up to date. Run `npm install` (or `npm ci` / `yarn install --frozen-lockfile`) before scanning to refresh the lockfile."
- In CI, run the scanner after `npm ci` or equivalent so the lockfile is the source of truth for that run.
- Optionally record the input file name and checksum in the report for traceability.

**Audit acceptability:** Auditors can treat the report as evidence for "what the lockfile declared at scan time" provided the process above is followed and documented.

---

## 2. Transitive Dependency Complexity

**Risk:** Large dependency trees (especially in Node) can mean hundreds of packages and many OSV API calls. Scans may be slow; reports may be long; rate limits or timeouts may occur.

**Mitigation:**

- Use OSV batch API (`/v1/querybatch`) where supported to reduce round-trips.
- Document that full-tree scanning is intentional for compliance (EO 14028, NIST SSDF) so that what you ship is fully visible.
- For very large monorepos, consider scanning per workspace with separate reports, or document scope (e.g. "root lockfile only") in the report.

**Audit acceptability:** Full transitive inclusion is aligned with "know what you ship"; limitations on size/speed are operational, not a reduction of scope for evidence.

---

## 3. False Positives and Incomplete Fixes

**Risk:** OSV or upstream advisories may contain errors, or "fixed_in" versions may be incomplete or wrong. A recommended upgrade might not fully fix the issue or might introduce regressions.

**Mitigation:**

- Recommend users verify fixes in a test environment before deploying.
- For uncertain cases, remediation text should say "Check references for upgrade or mitigation" and link to advisories.
- Do not claim that "recommended_action" is guaranteed correct; frame it as guidance derived from OSV data. Users remain responsible for validation.

**Audit acceptability:** Document this limitation in the report or user docs so that auditors understand that remediation guidance is advisory and should be validated.

---

## 4. Private and Internal Packages

**Risk:** Private or internal npm packages are not in the public npm registry or OSV. They will not be queried; the tool may report "no known vulnerabilities" for them, which could be misinterpreted as "verified safe" rather than "not in database."

**Mitigation:**

- Document clearly that only **public** packages (PyPI, npm public registry) are covered.
- Optionally list in the report packages for which OSV returned no result, so auditors can distinguish "no vulns" from "not in OSV."
- Do not claim coverage of private registries unless explicitly supported in a future version.

**Audit acceptability:** Stating scope (public ecosystems only) and optionally listing "not in OSV" packages makes the limitation explicit for evidence packages.

---

## 5. Multiple Lockfiles and Monorepos

**Risk:** A monorepo may have multiple package.json and lockfile pairs (e.g. apps/web, packages/shared). Scanning a single directory (e.g. repo root) may only scan one of them and miss others.

**Mitigation:**

- Document that `chifleton scan .` targets one directory. Users should run the scanner for each package root or provide multiple paths if the tool supports it in the future.
- If adding multi-path or workspace support, document which roots were scanned and merge or label results clearly in the report.

**Audit acceptability:** Scope of the scan (which directories were included) should be visible in the report or run documentation.

---

## 6. Yarn and pnpm Lockfile Formats

**Risk:** yarn.lock and pnpm-lock.yaml have different formats than package-lock.json. Parsing them requires separate logic. New lockfile versions (e.g. Yarn Berry, pnpm v9) may change format and break or misparse.

**Mitigation:**

- Implement and test each supported format; document supported lockfile versions in the user docs.
- If a format is not supported, fail with a clear message (e.g. "yarn.lock format v2 not yet supported") rather than silently misparsing.
- When upgrading support, add tests and note version support in release notes.

**Audit acceptability:** Documented support matrix and clear failure modes allow auditors to know what was actually scanned.

---

## 7. Remediation Heuristics

**Risk:** Remediation fields (priority, remediation_risk, recommended_action) are derived from heuristics (e.g. severity → priority, version delta → risk). They may not match organizational policy or actual upgrade impact.

**Mitigation:**

- Make priority and remediation_risk configurable or overridable in future (e.g. config file or CLI).
- State in docs that priority and risk are guidance only; organizations should align with their own risk taxonomy and change management.

**Audit acceptability:** Describing these as derived guidance (and optionally configurable) keeps evidence consistent with "advisory" rather than "guaranteed."

---

## Summary Table for Evidence Packages

| Risk | Mitigation (audit-acceptable) |
|------|-------------------------------|
| Lockfile stale | Run install/ci before scan; document in process; record input file in report. |
| Transitive complexity | Use batch API; document full-tree intent; scope per workspace if needed. |
| False positives / incomplete fixes | Verify in test env; "Check references" for uncertain cases; guidance is advisory. |
| Private packages | Document public-only scope; optionally list "not in OSV" packages. |
| Monorepos / multiple roots | Document single-dir scope; run per root or document paths. |
| Lockfile format changes | Document supported formats; fail clearly when unsupported. |
| Remediation heuristics | Document as guidance; allow future config/override. |

This document can be attached or linked from ASSESSMENT.md and security review packages to satisfy reviewer questions on risks and limitations.
