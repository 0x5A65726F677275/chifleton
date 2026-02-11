# Project Assessment: Software Supply Chain Security & Evidence Readiness

This document summarizes the **Chifleton** project’s purpose, scope, alignment with U.S. national policy, evidence-ready features, metrics, test coverage, and authorship. It supports technical evaluation, compliance documentation, and evidence-based review.

---

## One-Page Summary (for reviewers)

| Item | Summary |
|------|---------|
| **What it is** | Lightweight, open-source CLI that scans Python `requirements.txt` for known vulnerabilities via [OSV.dev](https://osv.dev) and produces terminal, HTML, and JSON reports. |
| **Why it matters** | Improves dependency vulnerability visibility for maintainers and small teams (including government, research, industry) who lack enterprise tooling; supports U.S. software supply chain security priorities. |
| **Policy alignment** | [Executive Order 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/) (know/document dependencies, transparent tooling); [NIST SSDF SP 800-218](https://csrc.nist.gov/publications/detail/sp/800-218/final) (vulnerability management, verifiable evidence); [CISA supply chain guidance](https://www.cisa.gov/topics/cyber-threats-and-advisories/software-supply-chain-security) (visibility, open tooling). |
| **Evidence-ready features** | Documented architecture ([ARCHITECTURE.md](ARCHITECTURE.md)) and project structure ([PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)); HTML report with summary, TOC, CVE/OSV IDs, remediation, author/timestamp/version in footer; JSON report for CI/compliance; single data source (OSV), local-only cache. |
| **Metrics** | Automated tests: parser (including pyproject.toml), OSV client, reporter, CLI e2e. See [METRICS.md](METRICS.md) for test cases and report validation. |
| **Authorship** | **Jaeha Yoo** — see [Attribution](#8-authorship--attribution). LICENSE, README, and report footer use consistent attribution. |
| **How to run** | `pip install .` then `chifleton scan requirements.txt --report html` or `--report json`. CI: [.github/workflows/scan.yml](../.github/workflows/scan.yml) (reports/ + artifact) or [dependency-scan.yml](../.github/workflows/dependency-scan.yml) (separate artifacts). Container: [Dockerfile](Dockerfile). |

---

## 1. Project Purpose and Scope

### Purpose

The **Chifleton** improves **dependency vulnerability visibility in the Python ecosystem**. It:

- Parses Python dependency files (e.g. `requirements.txt`).
- Queries [OSV (Open Source Vulnerabilities)](https://osv.dev) for known vulnerabilities affecting those packages and versions.
- Reports results in the terminal and as **evidence-ready** HTML and JSON outputs.

The project targets maintainers and small teams who need **transparent, auditable** dependency checks without proprietary services or complex setup.

### Scope (in scope / out of scope)

| In scope | Out of scope (current version) |
|----------|--------------------------------|
| Python `requirements.txt` and `pyproject.toml` [project.dependencies] | Other ecosystems (npm, etc.) |
| Single data source (OSV) | Multiple or proprietary vulnerability databases |
| CLI, HTML report, JSON report | SBOM generation, integrity/signature checks |
| Local SQLite cache | Remote or shared cache |
| Evidence-ready, audit-friendly design | Formal certification or third-party endorsement |

---

## 2. Alignment with U.S. Software Supply Chain Security Priorities

The project supports U.S. government priorities for securing the software supply chain and critical infrastructure.

### 2.1 Executive Order 14028 (Improving the Nation’s Cybersecurity)

[EO 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/) emphasizes securing the software supply chain and transparency. This project aligns by:

- **Knowing and documenting dependencies** — Identifies dependencies from `requirements.txt` and checks them against OSV; supports “know what you ship.”
- **Transparent tooling** — Single open data source (OSV), local-only cache; design documented in [ARCHITECTURE.md](ARCHITECTURE.md) and [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).
- **Evidence-ready artifacts** — HTML and JSON reports provide an auditable record (summary, CVE/OSV IDs, remediation) for security and compliance.

### 2.2 NIST Secure Software Development Framework (SSDF)

[NIST SSDF (SP 800-218)](https://csrc.nist.gov/publications/detail/sp/800-218/final) calls for managing vulnerabilities in dependencies and producing verifiable evidence. This project supports:

- **Identifying and managing vulnerabilities** — Surfaces known vulnerabilities (CVE/OSV IDs, severity, remediation) for dependencies.
- **Documentation and auditability** — Architecture and structure documented; reports are self-contained (HTML with print/PDF-friendly CSS) and machine-readable (JSON).

### 2.3 CISA Guidance (Software Supply Chain Security)

[CISA’s guidance](https://www.cisa.gov/topics/cyber-threats-and-advisories/software-supply-chain-security) stresses dependency and vulnerability visibility and open, transparent tooling. This project:

- **Reduces dependency blind spots** — Scans `requirements.txt` and reports vulnerabilities with CVE/OSV IDs and remediation.
- **Supports auditability** — Open-source implementation, single public data source, local-only cache; suitable for compliance-sensitive and government environments.

### 2.4 Policy-to-feature mapping

| Policy / guidance | Relevant clause or goal | Scanner feature that supports it |
|-------------------|-------------------------|-----------------------------------|
| **EO 14028** | Sec. 4(c) – provide a SBOM or equivalent; secure development practices | Dependency list from `requirements.txt` / `pyproject.toml`; vulnerability check against OSV; evidence-ready HTML/JSON reports. |
| **EO 14028** | Transparency, use of open standards | Single open data source (OSV); no proprietary feeds; documented architecture and data flow. |
| **NIST SSDF (SP 800-218)** | PW 6.1 – identify and manage vulnerabilities | Scan outputs CVE/OSV IDs, severity, remediation; reports suitable for vulnerability management workflows. |
| **NIST SSDF** | Verifiable evidence, documentation | HTML report (summary, TOC, per-package); JSON for automation; author, timestamp, scanner version in report metadata. |
| **CISA supply chain** | Dependency and vulnerability visibility | Scans dependencies; reports known vulns with IDs and references; usable in government and compliance-sensitive environments. |
| **CISA** | Open, transparent tooling | Open-source; single public API (OSV); local-only cache; no hidden or proprietary components. |

---

## 3. Remediation & Secure Usage

### Purpose

Chifleton is designed not only to detect known vulnerabilities in open-source dependencies, but to support secure, policy-aligned remediation and continuous improvement of software supply chains.

This approach aligns with U.S. government guidance emphasizing that vulnerability identification must be paired with documented response and risk management practices.

### Remediation Approach

For each identified vulnerability, Chifleton provides structured remediation guidance based on:

- Availability of a known fix
- Severity and exploitability
- Ecosystem-specific constraints (e.g., Python vs Node.js)
- Potential impact on system stability

Remediation recommendations are categorized to support consistent decision-making and auditability, including:

- **Upgrade to a fixed version**
- **Replace or remove** high-risk dependencies
- **Apply compensating controls** when fixes are unavailable
- **Document and monitor** accepted risk

Chifleton does not automatically modify dependencies. Instead, it produces evidence-ready outputs to support human review and accountable remediation decisions.

### Secure Usage Guidelines

Organizations using Chifleton are expected to integrate it into their secure software development lifecycle as follows:

- **Run dependency scans regularly** — At minimum: before release and after dependency changes. Recommended: automated execution in CI/CD pipelines.
- **Prioritize remediation based on risk** — Address Critical and High severity issues with available fixes promptly. Track Medium and Low severity issues in backlog or risk registers.
- **Document remediation decisions** — Record applied fixes, deferred actions, or accepted risks. Maintain records for audit and compliance review.
- **Manage no-fix vulnerabilities** — Identify compensating controls; periodically reassess risk as dependency updates become available.
- **Reduce systemic supply chain risk** — Minimize unnecessary dependencies; prefer actively maintained and widely adopted libraries; enforce lockfiles to ensure reproducibility.

### Policy Alignment

This remediation and secure usage model supports the following U.S. supply chain security objectives:

- **Executive Order 14028** — Improves visibility into software dependencies and supports accountable vulnerability response.
- **NIST Secure Software Development Framework (SP 800-218)** — PW.4: Identify and confirm vulnerabilities and remediate them; RV.1 & RV.2: Maintain vulnerability response processes and evidence.
- **CISA Secure Software Guidance** — Encourages proactive dependency management, transparency, and documented risk decisions.

### Evidence-Ready Design

Chifleton remediation outputs are structured to support:

- Third-party audits
- Government security reviews
- Internal risk governance
- SBOM and vulnerability management workflows

By combining detection with remediation guidance and secure usage practices, Chifleton contributes to reducing systemic software supply chain risk.

---

## 4. Evidence-Ready Features

| Feature | Description |
|--------|-------------|
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md): technology choices (Python, OSV, SQLite, monolithic CLI) and rationale. |
| **Project structure** | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md): flow (CLI → Parser → Cache/OSV → Reporter), separation of concerns. |
| **HTML report** | Summary (packages scanned, vulnerable count, total vulns); table of contents with anchors (`#pkg-...`); per-package sections with CVE/OSV IDs, severity, references, remediation; full-width, print/PDF-friendly CSS; self-contained (no external CSS/JS). |
| **Report metadata** | Footer: author name, generation timestamp (UTC), scanner version for traceability. |
| **JSON report** | Machine-readable output (`report` + `packages`) for CI/CD and compliance pipelines. |
| **CLI** | Exit codes (0 success, 1 error); `--report html`, `--report json`, `--no-cache`; suitable for scripting and CI. |
| **Single data source** | OSV only; local SQLite cache; no proprietary feeds. |

---

## 5. Sample Metrics and Test Coverage

### Sample metrics (illustrative)

When actual usage data is not yet collected, the following **example** values can be used in documentation or evidence. Replace with real numbers when available.

| Metric | Example value | Notes |
|--------|----------------|-------|
| Packages scanned (per run) | 4–12 | Typical small Python project `requirements.txt`. |
| Vulnerabilities detected (per run) | 0–3 | Depends on dependency versions and OSV data. |
| Total scans run (cumulative) | e.g. 50 | Local + CI runs. |
| Test cases (automated) | 28 | Parser (12, incl. pyproject.toml), OSV client (5), reporter (6), CLI e2e (5). |

See [METRICS.md](METRICS.md) for suggested test cases and narrative.

### Test coverage summary

| Area | Tests | What is covered |
|------|-------|------------------|
| Parser | 12 | requirements.txt: empty, comments, `package==version`, package-only, inline comments, `-r`/`-e` skipped, file read; pyproject.toml: empty project, no deps, with dependencies; parse_dependency_file dispatch. |
| OSV client | 5 | Empty/error response handling; `query_vulnerabilities` with mocked HTTP (with/without version). |
| Reporter | 6 | `_enrich_results`; HTML summary/footer/author/version; JSON structure and counts. |
| CLI (e2e) | 5 | File not found (exit 1); empty requirements (exit 0); HTML/JSON output with mocked OSV; pyproject.toml scan; vuln content in reports. |

Run tests: `pip install -e ".[dev]"` then `pytest tests/ -v`.

---

## 6. Rationale: Contribution to National Cybersecurity

- **Critical need** — Software supply chain vulnerabilities pose a major risk to U.S. digital infrastructure. This tool makes dependency vulnerability analysis accessible to teams without enterprise tooling.
- **Scale and accessibility** — Python is widely used in government, research, and industry. A simple, open-source scanner that runs in CI and produces evidence-ready reports supports broader visibility.
- **Risk mitigation** — Surfaces known vulnerabilities (CVE/OSV IDs, remediation) so maintainers can patch or replace dependencies; transparent design supports audit and compliance.
- **Policy alignment** — Aligns with EO 14028, NIST SSDF, and CISA guidance on supply chain security, dependency visibility, and transparent, auditable tooling.

---

## 7. Five Independent Review Passes

### Pass 1 — Security & Supply Chain Impact

- **Strengths:** Single public data source (OSV), local-only cache, no hidden services; documented, auditable design.
- **Gaps:** Python/`requirements.txt` only; no SBOM; security contact in SECURITY.md should be a real process (see [SECURITY.md](SECURITY.md)).
- **Verdict:** Strong alignment for the scoped use case.

### Pass 2 — Usability & Adoption

- **Strengths:** One-command install, HTML and JSON reports, GitHub Actions, Docker, README and docs.
- **Gaps:** No PyPI publish yet; adoption metrics would strengthen impact narrative.
- **Verdict:** Good usability and adoption potential.

### Pass 3 — Documentation & Evidence Readiness

- **Strengths:** README, ARCHITECTURE, PROJECT_STRUCTURE, SECURITY, this assessment; HTML/JSON with metadata; one-page summary above.
- **Gaps:** None material for documentation.
- **Verdict:** Documentation supports evidence and audit use.

### Pass 4 — Policy Alignment

- **Strengths:** Explicit EO 14028, NIST SSDF, CISA references in README and this document; clear link to policy goals.
- **Gaps:** Optional: policy-to-feature mapping table.
- **Verdict:** Policy alignment clearly stated.

### Pass 5 — Completeness and Risk Gaps

- **Strengths:** Working scanner, 22 tests, CI workflow, Docker, unified attribution, report metadata.
- **Gaps:** No SBOM; no multi-ecosystem support; SECURITY.md contact must be replaced with repository-specific process before production use.
- **Verdict:** Complete for stated scope; remaining gaps in TODO below.

---

## 8. Authorship / Attribution

- **Author / maintainer:** **Jaeha Yoo**
- **License:** MIT. See repository [LICENSE](../LICENSE) (Copyright (c) 2026 Jaeha Yoo).
- **README:** Project overview and national-interest section reference the project; full assessment in this document. Attribution is consistent with LICENSE and report footer.
- **Report footer (HTML/JSON):** “Report generated by [author], [year]” with scanner version and UTC timestamp. Author and version are set from package metadata (`scanner.__author__`, `scanner.__version__`).

Consistent attribution across LICENSE, README, and report outputs supports evidence and audit use.

---

## 8. Prioritized TODO for Evidence-Based Evaluation

Improvements ordered by impact on supply chain security, evidence readiness, and adoption. Each item references relevant files.

### High priority

1. **Replace SECURITY.md contact with repository-specific process**  
   - **File:** [SECURITY.md](SECURITY.md)  
   - **Action:** Use GitHub Security Advisories (or a real maintainer contact). See current SECURITY.md for placeholder replacement instructions.  
   - **Rationale:** Required for responsible disclosure and production use.

2. **Publish to PyPI**  
   - **Files:** [pyproject.toml](pyproject.toml), [README.md](README.md)  
   - **Action:** Publish package so users can `pip install chifleton`; document in README.  
   - **Rationale:** Maximizes adoption and visibility.

3. **Collect and document real usage metrics**  
   - **Files:** [METRICS.md](METRICS.md), [ASSESSMENT.md](ASSESSMENT.md)  
   - **Action:** When available, replace example metrics with real counts (scans run, packages scanned, vulnerabilities found).  
   - **Rationale:** Strengthens impact narrative for evidence-based evaluation.

### Medium priority

4. **Support `pyproject.toml` dependencies**  
   - **Files:** [scanner/parser.py](scanner/parser.py), [tests/test_parser.py](tests/test_parser.py)  
   - **Action:** Parse `[project.dependencies]` (or equivalent) in addition to `requirements.txt`.  
   - **Rationale:** Broader coverage without changing architecture.

5. **Optional: SBOM output**  
   - **Files:** [scanner/reporter.py](scanner/reporter.py), [scanner/cli.py](scanner/cli.py)  
   - **Action:** Add minimal SBOM (e.g. CycloneDX/SPDX) for integration with supply chain tooling.  
   - **Rationale:** Aligns with EO 14028 and broader supply chain automation.

6. **Policy-to-feature mapping table**  
   - **File:** [ASSESSMENT.md](ASSESSMENT.md) (or README)  
   - **Action:** Optional table mapping EO 14028 / NIST SSDF / CISA clauses to specific scanner features.  
   - **Rationale:** Makes policy alignment even easier for reviewers.

### Lower priority

7. **Multi-ecosystem support**  
   - **Files:** [scanner/parser.py](scanner/parser.py), [scanner/osv_client.py](scanner/osv_client.py)  
   - **Action:** Consider other ecosystems (e.g. npm) if roadmap expands.  
   - **Rationale:** Broader impact; larger scope.

8. **Endorsements or case studies**  
   - **Files:** [README.md](README.md), [ASSESSMENT.md](ASSESSMENT.md)  
   - **Action:** When available, add “Used by” or short case studies with permission.  
   - **Rationale:** Third-party validation for evidence packages.

---

## References to Generated and Modified Files

| File | Role |
|------|------|
| [ASSESSMENT.md](ASSESSMENT.md) | This document: purpose, scope, policy alignment, evidence features, metrics, test coverage, authorship, review passes. |
| [README.md](README.md) | Install, CLI, output formats, policy refs (EO 14028, NIST SSDF, CISA), CI/Docker, project structure, ASSESSMENT link. |
| [METRICS.md](METRICS.md) | Example metrics and suggested test cases for reports. |
| [SECURITY.md](SECURITY.md) | Responsible disclosure; maintainer contact in README/ASSESSMENT; GitHub Security Advisories. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design decisions and evidence-readiness rationale. |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Flow and file roles. |
| [.github/workflows/dependency-scan.yml](../.github/workflows/dependency-scan.yml) | GitHub Actions: scan on push/PR, HTML + JSON artifacts. |
| [Dockerfile](Dockerfile) | Containerized execution. |
| [scanner/cli.py](scanner/cli.py) | CLI with `--report html`, `--report json`, `--no-cache`. |
| [scanner/reporter.py](scanner/reporter.py) | Terminal, HTML, JSON reporting; timestamp, version, author in reports. |
| [scanner/templates/report.html.jinja](scanner/templates/report.html.jinja) | HTML template: summary, TOC anchors, footer (author, year, version, timestamp), print-friendly CSS. |
| [LICENSE](../LICENSE) | MIT; Copyright (c) 2026 Jaeha Yoo. |

---

*This assessment supports technical evaluation, compliance documentation, and evidence-based review. For run instructions and policy links, see the [One-Page Summary](#one-page-summary-for-reviewers) and [README.md](README.md).*
