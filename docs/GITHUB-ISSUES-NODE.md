# GitHub issues checklist: Node.js support

Use this list to create discrete issues from [DESIGN-NODE.md](DESIGN-NODE.md). Each item can be one issue or a parent issue with sub-tasks.

---

- [ ] **Parser: package-lock.json** — Parse npm v7+ `packages` map; return list of (name, version); handle root package; add tests.
- [ ] **Parser: yarn.lock** — Parse yarn.lock format; return (name, version); document supported format version; add tests.
- [ ] **Parser: pnpm-lock.yaml** — Parse pnpm-lock.yaml; return (name, version); add tests.
- [ ] **Parser: package.json (no lockfile)** — Parse dependencies/devDependencies; resolve versions or report “declared only”; warn in UI when no lockfile.
- [ ] **OSV client: ecosystem parameter** — Add `ecosystem` arg to `query_vulnerabilities()` (default `PyPI`); use `npm` for Node path; keep `get_vulns_from_response` unchanged.
- [ ] **Cache: ecosystem in key** — Add `ecosystem` to cache table (primary key or column); migration for existing DB (default PyPI); update get/set calls.
- [ ] **CLI: ecosystem detection** — For `scan .`, detect Node vs Python from directory contents; add `--ecosystem node|python`; prefer lockfile when present.
- [ ] **CLI: scan package.json / lockfiles** — Route `scan package.json`, `scan package-lock.json`, etc., to Node parser and OSV(npm).
- [ ] **Reporter: optional ecosystem field** — Add `ecosystem` to result dict and JSON output; in HTML, show Ecosystem column when multiple ecosystems or always for npm.
- [ ] **Docs: README** — Document Node usage (scan package.json, scan ., --ecosystem); lockfile preference; example commands.
- [ ] **Docs: ASSESSMENT.md** — Merge [ASSESSMENT-NODE-UPDATE.md](ASSESSMENT-NODE-UPDATE.md): scope table, Node policy subsection, evidence-ready row.
- [ ] **Tests: Node parser** — Unit tests for each lockfile/package.json format; fixture files.
- [ ] **Tests: CLI** — E2E: `scan package-lock.json` (mocked OSV) produces HTML/JSON; `scan .` with only package.json runs Node path.
- [ ] **Limitations: document** — In README or docs, document lockfile freshness, private packages, multiple roots, unsupported lockfile versions; audit recommendations.

Optional follow-ups:

- [ ] **OSV querybatch** — Use POST /v1/querybatch for Node scan when many packages; reduce round-trips.
- [ ] **Monorepo / multiple roots** — Support scanning multiple directories and merging into one report (e.g. `--all` or list of paths).
