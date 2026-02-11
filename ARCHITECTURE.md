# Architecture and design decisions

This document records the main architecture and technology choices for Chifleton. It is intended to support **evidence-readiness** for audit and policy review by making the rationale for key decisions explicit.

---

## Why Python was chosen

- **Accessibility:** Python is widely taught, has a low barrier to entry, and is one of the most adopted languages in the United States and globally. This makes the project approachable for maintainers and contributors.
- **Ecosystem fit:** The scanner targets Python dependency files first (`requirements.txt`); implementing it in Python keeps the tool in the same ecosystem it secures and simplifies parsing and tooling.
- **Adoption and portability:** Python runs on major operating systems and in CI environments (e.g., GitHub Actions) with minimal setup, supporting broad use without lock-in to a single platform.

---

## Why OSV.dev was chosen

- **Open and standardized:** OSV (Open Source Vulnerabilities) provides a public, well-documented API and a standardized schema for vulnerabilities. There is no dependency on proprietary or paid vulnerability databases.
- **Backing and sustainability:** OSV is backed by Google and used across the open-source ecosystem, which supports long-term availability and quality of data.
- **Transparency:** Using a single, well-known data source makes it clear where vulnerability information comes from and how to verify or dispute it.

---

## Why a monolithic CLI was chosen over microservices

- **Simplicity:** A single CLI application is easier to install, run, and reason about. There are no distributed components, network configuration, or service discovery.
- **Operational burden:** Microservices would require multiple processes, deployment coordination, and often a network or message layer—unnecessary for a tool that parses a file, calls one external API, and writes local output.
- **CI and scripting:** A single command (`scanner scan`) is straightforward to integrate into scripts and CI (e.g., GitHub Actions) without orchestrating several services.

---

## Why a local SQLite cache was chosen

- **No external database:** The scanner does not depend on or deploy any external database. SQLite is process-local and file-based, which simplifies deployment and avoids operational or compliance concerns around third-party data stores.
- **Performance and politeness:** Caching OSV responses reduces repeated API calls for the same package/version, improving run time and reducing load on OSV.
- **Transparency and control:** The cache is stored in the user’s home directory (e.g., `~/.chifleton/`). Users can inspect or clear it; there is no hidden or remote persistence beyond this local file.

---

## Component overview

| Component   | Responsibility |
|------------|----------------|
| `cli.py`   | Entry point; `scanner scan` with `--report` and `--no-cache`; coordinates parser, cache, OSV client, and reporter. |
| `parser.py`| Parses `requirements.txt` (e.g., `package==version`, `package`); ignores comments and empty lines. |
| `osv_client.py` | Calls OSV.dev `/v1/query` with PyPI ecosystem; handles errors and empty results. |
| `cache.py` | SQLite table `osv_cache(pkg, version, response_json, fetched_at)`; lookup before remote calls when cache is enabled. |
| `reporter.py` | Rich-based terminal output; Jinja2-based HTML report with summary, per-package tables, CVE/OSV IDs, references, remediation. |
| `utils.py` | Path resolution for the requirements file (default: `requirements.txt` in cwd). |

Data flow: **CLI** → **parser** (deps) → for each dep: **cache** (if enabled) else **osv_client** → **reporter** (terminal and optionally HTML).
