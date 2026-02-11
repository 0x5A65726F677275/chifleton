# Policy and Compliance Mapping (ASSESSMENT.md)

The following text is suitable for inclusion in **ASSESSMENT.md** to explicitly map Chifleton capabilities to U.S. federal software assurance and supply chain guidance. Use it for security review documents and evidence packages.

---

## Detection → EO 14028 (Visibility, Transparency)

| EO 14028 goal | Chifleton capability |
|---------------|------------------------|
| **Know and document dependencies** | Dependency list from lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml) or declaration files (requirements.txt, pyproject.toml, package.json). Full transitive tree when using lockfiles. |
| **Transparency** | Single open data source (OSV.dev); no proprietary feeds. Architecture and data flow documented (ARCHITECTURE.md, DESIGN-NODE.md, DESIGN-REMEDIATION-AND-NODE.md). |
| **Evidence-ready artifacts** | HTML and JSON reports with summary, package list, CVE/OSV IDs, severity, remediation, timestamp, scanner version, and author. |

---

## Remediation → NIST SSDF PW.4, RV.1, RV.2

| NIST SSDF practice | Chifleton capability |
|--------------------|----------------------|
| **PW.4** (Produce well-secured software) | Vulnerability detection and remediation guidance support producing software with known dependencies and known risks addressed. |
| **RV.1** (Identify vulnerabilities) | Scan results identify known vulnerabilities (CVE/OSV IDs, severity) in dependencies (direct and transitive). |
| **RV.2** (Analyze and determine risk) | Per-vulnerability remediation intelligence: fix availability, recommended action, priority (Immediate/Planned/Monitor), and remediation risk (breaking-change likelihood). Supports risk-based triage and documented decisions. |
| **Verifiable evidence** | Reports include fixable vs non-fixable counts, recommended actions, and metadata for audit trail. |

---

## Improvement Guidance → CISA Secure Software Practices

| CISA / secure software goal | Chifleton capability |
|-----------------------------|------------------------|
| **Dependency and vulnerability visibility** | Scans Python and Node.js ecosystems; reports all findings with severity and remediation. |
| **Project-level improvements** | Optional improvement checklist (--include-guidance): lockfile enforcement, reduce sprawl, remove unmaintained packages, pin versions, automated updates, SBOM in CI. Classified by security impact and effort. |
| **Documentation and process** | Secure supply chain guidelines (docs/SECURE-SUPPLY-CHAIN-GUIDELINES.md) cover: what to do after a scan, scan frequency, documenting remediation decisions, no-fix vulns, legacy deps, business risk exceptions. Suitable for ASSESSMENT.md and internal SDLC policies. |

---

## Summary Table for Evidence Packages

| Area | Policy / guidance | Feature |
|------|-------------------|---------|
| **Detection** | EO 14028 | Dependency list from lockfile/declaration files; OSV-based vulnerability check; evidence-ready HTML/JSON. |
| **Remediation** | NIST SSDF PW.4, RV.1, RV.2 | Remediation intelligence (fix_available, recommended_action, priority, remediation_risk) per vulnerability. |
| **Improvement** | CISA Secure Software | Improvement recommendations and secure supply chain guidelines (--include-guidance). |

---

*Merge the above into ASSESSMENT.md under a new subsection (e.g. "Policy and Compliance Mapping") or append to the existing policy-to-feature mapping table.*
