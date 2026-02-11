# Secure Supply Chain Guidelines (Audit-Ready)

This section is suitable for inclusion in ASSESSMENT.md, security review documents, and internal SDLC policies. It explains what developers and maintainers should do after running Chifleton and how to document and handle exceptions.

---

## What to Do After Running Chifleton

1. **Triage results**  
   Review the report (HTML or JSON) for vulnerabilities. Prioritize by severity (Critical, High, then Medium/Low). Use the remediation guidance (recommended action, fix availability, priority) to decide order of work.

2. **Remediate where possible**  
   For each finding with a recommended action (e.g. "Upgrade to >=X.Y.Z"), apply the change in a branch, run tests, and update the dependency file or lockfile. Commit the fix with a reference to the vulnerability ID (CVE or OSV) in the commit message or linked ticket.

3. **Document decisions**  
   For every vulnerability that is **not** remediated immediately (e.g. deferred, accepted risk, or no fix available), record the decision in a consistent place: ticket system, SECURITY.md, or an exception register. Include: vulnerability ID, package and version, reason for deferral or exception, and review/expiry date if applicable.

4. **Re-scan**  
   After changing dependencies or lockfiles, run Chifleton again to confirm new versions are in use and that findings are resolved or acknowledged.

---

## How Often to Run Scans

- **On every pull request** that changes dependency files or lockfiles (recommended for CI).
- **Nightly or on schedule** for visibility on default branches.
- **Before release** as a gate: e.g. fail the build if `--fail-on critical` (or `high`) is set and findings exist, unless an exception is documented.

Retain scan reports (HTML/JSON) with timestamps for audits and compliance evidence.

---

## Documenting Remediation Decisions

- **Fixed:** Document in the change (commit/ticket) the vulnerability ID and the action taken (e.g. "Upgrade lodash to 4.17.21 (GHSA-xxx)").
- **Deferred:** Record in a central list or ticket: CVE/OSV ID, package, version, planned remediation date, and owner.
- **Accepted risk:** Document justification, risk level, and approval (e.g. from security or project lead). Set a review date.
- **No fix available:** Record the finding and that no upstream fix exists; consider workarounds or alternative packages and document that decision.

---

## No-Fix Vulnerabilities

When a vulnerability has **no known fix** (fix_available is false):

- Confirm in the advisory and references that no patched version exists.
- Evaluate workarounds (config, network controls, or replacing the dependency).
- Document the finding and the decision (accept, replace, or mitigate) in your exception register or security documentation.
- Re-scan when new versions or advisories appear; OSV and upstream advisories are updated over time.

---

## Legacy Dependencies

For old or unmaintained packages:

- Prefer upgrading or replacing with a maintained alternative. If that is not feasible, document the business/technical reason and the risk.
- Apply other controls (e.g. network segmentation, least privilege) where possible.
- Schedule periodic review and re-evaluation; include in your vulnerability management process.

---

## Business Risk Exceptions

When business needs require running a known vulnerable dependency (e.g. critical legacy system):

- **Document:** Vulnerability ID, package, version, business justification, risk level, and who approved.
- **Time-bound:** Set an expiry or review date and reassess.
- **Compensating controls:** Describe any mitigations (monitoring, network controls, limited exposure).
- **Traceability:** Link to your SDLC or risk register so auditors can see the exception and its approval.

---

## Policy Alignment (Summary)

- **EO 14028:** Knowing and documenting dependencies; transparent, evidence-ready tooling. These guidelines support that by defining how to act on scan results and document exceptions.
- **NIST SSDF (PW.4, RV.1, RV.2):** Identifying and analyzing vulnerabilities and responding with remediation or documented decisions. The steps above align with RV practices.
- **CISA Secure Software:** Dependency visibility and proactive management. Running scans regularly and documenting remediation and exceptions supports CISA guidance.

Use this text verbatim or adapt it to your organization’s policy names and approval requirements. For full policy-to-feature mapping, see ASSESSMENT.md.
