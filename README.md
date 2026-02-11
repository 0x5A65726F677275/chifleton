# Chifleton

**Dependency vulnerability scanner for U.S. software supply chain security** — aligned with Executive Order 14028, NIST SSDF, and CISA guidance.

## Project Overview

**Chifleton (formerly Chifleton)** is a lightweight, open-source supply chain attack vector visibility engine built on OSV. It scans dependency files for known vulnerabilities using [OSV.dev](https://osv.dev) and generates evidence-ready reports in the terminal or as HTML/JSON outputs, supporting policy-aligned security workflows.

**Python:** `requirements.txt`, `pyproject.toml` (`project.dependencies`)  
**Node.js:** `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`  
_(Lockfiles are preferred for resolved versions.)_

Designed for maintainers and small teams, Chifleton provides transparent dependency security checks without proprietary services or complex setup.


---

## Quick Start

```bash
pip install .
chifleton scan requirements.txt --report html
# Open scan-report.html
```

1. **Install** (from the project directory):

   ```bash
   pip install .
   ```

2. **Create a sample `requirements.txt`** (or use your own):

   ```text
   requests>=2.28
   Jinja2>=3.1
   ```

3. **Run a scan** (generates HTML + JSON by default) and open the report:

   ```bash
   chifleton scan requirements.txt
   # or: python -m scanner scan requirements.txt
   ```
   Then open **`scan-report.html`** in your browser.

4. Open **`scan-report.html`** in your browser to view the summary, table of contents, and per-package vulnerability details.

### Example commands (copy & paste)

```bash
# Scan current dir requirements.txt → terminal + scan-report.html + scan-report.json
chifleton scan
# Same without PATH: python3 -m chifleton scan

# Scan a specific file
chifleton scan path/to/requirements.txt
chifleton scan pyproject.toml
chifleton scan package.json
chifleton scan package-lock.json

# Scan installed packages (exact versions)
pip freeze | chifleton scan - --from-freeze

# Terminal only, no files
chifleton scan --report none

# CI: exit 1 if any vulnerability found
chifleton scan --fail-on-vuln

# Force fresh API calls (no cache)
chifleton scan --no-cache
```

---

## Installation

Requires **Python 3.10+**.

### Install without cloning (use as a binary)

To use the `chifleton` command globally without cloning the repo:

```bash
# From GitHub (no clone)
pip install "git+https://github.com/0x5A65726F677275/Chifleton.git"
# Or
pipx install "git+https://github.com/0x5A65726F677275/Chifleton.git"
```

Then run from any directory:

```bash
chifleton scan requirements.txt --report html
chifleton scan package-lock.json
```

### Install from source (clone 후)

| Method | Command | Use case |
|--------|---------|----------|
| **Install from current directory** | `pip install .` | Normal use; installs the `chifleton` command. |
| **Editable install (development)** | `pip install -e ".[dev]"` | Work on the code; includes pytest. |

Run from the project root. If `chifleton` is not on your PATH, use **`python3 -m chifleton scan`** or `python3 -m scanner scan` (after installing in a venv, see below).

**Linux / WSL (Ubuntu/Debian):**

- **`error: externally-managed-environment`** — System Python blocks `pip install .`. Use one of these:

  **Option A — Virtual environment (recommended):**
  ```bash
  cd /path/to/chifleton
  python3 -m venv .venv
  source .venv/bin/activate
  pip install .
  chifleton scan
  ```

  **Option B — pipx (installs `chifleton` in an isolated env, no venv needed):**
  ```bash
  sudo apt install -y pipx   # if needed
  pipx ensurepath             # add to PATH
  cd /path/to/chifleton
  pipx install .
  chifleton scan
  ```

- **`chifleton: command not found`** — Install in that environment (venv or pipx above), or from an activated venv run: **`python3 -m chifleton scan`** (or `python3 -m scanner scan`).
- **`pip` not found** — Install: `sudo apt update && sudo apt install -y python3-pip python3-venv`

---

## CLI Usage

The only subcommand is **`scan`**. It takes an optional path to a dependency file (default: `requirements.txt` in the current directory). **Supported inputs:** **Python** — `requirements.txt`, `pyproject.toml` ([project.dependencies]), pip-freeze style via `--from-freeze`; **Node.js** — `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` (lockfile preferred for exact versions).

### Basic commands

| Action | Command |
|--------|---------|
| Scan default `requirements.txt` | `chifleton scan` |
| Scan a specific file | `chifleton scan path/to/requirements.txt`, `chifleton scan pyproject.toml`, `chifleton scan package.json`, `chifleton scan package-lock.json` |
| Scan **installed** packages (pip freeze) | `pip freeze \| chifleton scan - --from-freeze` or `chifleton scan frozen.txt --from-freeze` |
| Generate HTML + JSON (default) | `chifleton scan` (writes both) |
| Terminal-only (no report files) | `chifleton scan --report none` |
| Bypass cache (always query OSV) | `chifleton scan --no-cache` |
| CI: fail build if vulns found | `chifleton scan --fail-on-vuln` |

### Options

| Option | Values | Description |
|--------|--------|-------------|
| `--report` | `html`, `json`, `none` | **Default: both `html` and `json`.** `html` → `scan-report.html`; `json` → `scan-report.json`; `none` → terminal only. |
| `--no-cache` | flag | Disable the local SQLite cache; every run queries the OSV API for each package. |
| `--from-freeze` | flag | Input is pip-freeze style (`name==version` per line). Use path `-` or omit to read from stdin. |
| `--fail-on-vuln` | flag | Exit with code 1 if any vulnerability is found (for CI). |

### Examples

```bash
# Default: terminal + HTML + JSON
chifleton scan

# Terminal-only output
chifleton scan --report none

# Scan actually installed versions (recommended for accurate daily checks)
pip freeze | chifleton scan - --from-freeze
# or save first:
pip freeze > frozen.txt && chifleton scan frozen.txt --from-freeze

# CI: fail the job when vulnerabilities exist
chifleton scan requirements.txt --fail-on-vuln

# Fresh data, no cache (e.g. after OSV updates)
chifleton scan --no-cache --report html
```

### Testing and usage (sample commands)

```bash
# Run all tests (from project directory)
pip install -e ".[dev]"
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=scanner --cov-report=term-missing

# Quick smoke test: scan and open report
chifleton scan requirements.txt --report html
# then open scan-report.html in your browser
```

---

## Output

### Terminal

Colored summary with per-package results: CVE/OSV IDs, short summary, and remediation hints. A summary table lists all packages with vulnerabilities.

### HTML report

Use `--report html` to generate **`scan-report.html`** in the same directory as the scanned file. The report includes:

- **Summary** — Total packages scanned, packages with vulnerabilities, and total vulnerability count.
- **Table of contents** — Clickable links to each package section (useful for long reports).
- **Per-package sections** — Each dependency in its own block with vulnerability count, CVE/OSV IDs, severity (when available), references, and remediation.
- **Full-width layout** — Readable on large screens; content is not overly constrained.
- **Print / PDF-friendly CSS** — When printing or saving as PDF: high-contrast text, minimal background color, page breaks between package sections, and link URLs shown after link text.
- **Footer attribution** — “Report generated by Chifleton — Author: Jaeha Yoo” with generation timestamp (UTC) and version; data-source credit (OSV).

The HTML file is self-contained (no external CSS or JavaScript) and suitable for sharing, archiving, or use as supporting evidence.

### JSON report

Use `--report json` to generate **`scan-report.json`** in the same directory as the scanned file. The JSON includes a `report` object (e.g. `generated_at`, `scanner_version`, `package_count`, `total_vulnerabilities`) and a `packages` array with per-package vulnerability details (ids, summary, references, remediation, severity) for use in CI/CD and compliance tooling.

---

## Data source

Vulnerability data comes from [OSV (Open Source Vulnerabilities)](https://osv.dev), an open, Google-backed database with a standardized API. No proprietary or paid feeds are used.

---

## Project structure (for reviewers and new contributors)

High-level layout of the repository:

| Path | Purpose |
|------|---------|
| **`scanner/`** | Main Python package: CLI, parser, OSV client, cache, reporter, and HTML template. |
| **`scanner/templates/`** | Jinja2 template for the HTML report (bundled so `pip install .` works). |
| **`templates/`** | Same report template at repo root (for development); keep in sync with `scanner/templates/`. |
| **`tests/`** | Pytest tests for parser, OSV client, reporter, and CLI. |
| **`ARCHITECTURE.md`** | Design decisions (Python, OSV, SQLite, monolithic CLI). |
| **`PROJECT_STRUCTURE.md`** | Detailed “how it fits together” guide. |
| **`ASSESSMENT.md`** | Project assessment: policy alignment (EO 14028, NIST SSDF, CISA), evidence-ready features, metrics, authorship. |
| **`METRICS.md`** | Test metrics and suggested test cases for reports. |
| **`SECURITY.md`** | How to report security issues (responsible disclosure; GitHub Security Advisories or maintainer). |
| **`Dockerfile`** | Container build for running Chifleton. |
| **`pyproject.toml`** | Package metadata, dependencies, and the `chifleton` console script. |
| **`requirements.txt`** | Example dependency file; you can run `chifleton scan requirements.txt` to try the tool. |

For a deeper walkthrough, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

---

## National interest and software supply chain security

This project contributes to **U.S. software supply chain security** and addresses **critical supply chain risk** in line with U.S. policy and guidance:

- **[Executive Order 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/)** — Improving the Nation’s Cybersecurity: Chifleton supports knowing and documenting dependencies and using transparent, evidence-ready tooling.
- **[NIST Secure Software Development Framework (SSDF), SP 800-218](https://csrc.nist.gov/publications/detail/sp/800-218/final)** — Identifying and managing vulnerabilities in dependencies and producing verifiable, auditable evidence (reports with CVE/OSV IDs, severity, remediation).
- **[CISA software supply chain security guidance](https://www.cisa.gov/topics/cyber-threats-and-advisories/software-supply-chain-security)** — Dependency and vulnerability visibility and use of open, transparent tooling.

Project contributions:

- **Transparent, open-source tooling** — No proprietary vulnerability databases or hidden services; a single open data source (OSV) and local-only cache support auditability and use in compliance-sensitive environments.
- **Evidence-ready reporting** — HTML and JSON reports provide a clear, printable and machine-readable record of dependency checks (summary, per-package results, CVE/OSV IDs, remediation, timestamp, version), suitable for security review and documentation.
- **Target users** — Maintainers and small teams who may not have access to enterprise vulnerability management, including in government, research, and industry.

For repository-level assessment (policy alignment, evidence-ready features, metrics, attribution), see the root [ASSESSMENT.md](../ASSESSMENT.md). For detailed in-repo assessment, see [ASSESSMENT.md](ASSESSMENT.md) in this directory.

---

## CI and automation

### GitHub Actions

Workflows run Chifleton on push and pull requests and publish reports:

- **[.github/workflows/scan.yml](../.github/workflows/scan.yml)** — Installs Chifleton, runs `chifleton scan requirements.txt --report html` and `--report json`, writes reports into the repository **`reports/`** folder, and uploads them as workflow artifacts (`scan-reports`).
- **[.github/workflows/dependency-scan.yml](../.github/workflows/dependency-scan.yml)** — Same scan; uploads `scan-report.html` and `scan-report.json` from the project directory as separate artifacts.

To use in your repo: copy the workflow and set `working-directory` to the path containing your `requirements.txt`, or run `chifleton scan path/to/requirements.txt --report html` from repo root.

### Docker

Build and run Chifleton in a container:

```bash
# From the project directory
docker build -t chifleton .

# Scan requirements.txt in the current directory (mount current dir as /work)
docker run --rm -v "$(pwd):/work" -w /work chifleton scan /work/requirements.txt --report html

# Or use default command (scans requirements.txt in /work)
docker run --rm -v "$(pwd):/work" -w /work chifleton
```

Reports are written into the mounted directory. For JSON: add `--report json` or run the scan twice (once `html`, once `json`).

---

## Author / attribution

**Author:** Jaeha Yoo.  
Attribution is consistent across the repository [LICENSE](../LICENSE), this README, and the HTML/JSON report footers (Chifleton, author name, version, generation timestamp). For full authorship and evidence context, see the root [ASSESSMENT.md](../ASSESSMENT.md) (Author attribution and contact) or this directory’s [ASSESSMENT.md](ASSESSMENT.md) § Authorship / attribution.

---

## License

MIT. See the repository [LICENSE](../LICENSE) file.
