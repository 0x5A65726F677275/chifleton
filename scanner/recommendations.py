"""Project-level improvement recommendations for secure supply chain."""

from typing import Any

# Recommendation: id, title, description, security_impact, effort, policy_relevance
RECOMMENDATIONS: list[dict[str, Any]] = [
    {
        "id": "lockfile-enforcement",
        "title": "Enable lockfile enforcement",
        "description": "Run installs with lockfile-only (e.g. npm ci, yarn install --frozen-lockfile, pip install from requirements.txt with hashes). Fail CI if lockfile is out of date.",
        "security_impact": "High",
        "effort": "Low",
        "policy_relevance": "EO 14028, NIST SSDF",
    },
    {
        "id": "reduce-sprawl",
        "title": "Reduce dependency sprawl",
        "description": "Audit and remove unused or duplicate packages. Prefer fewer, well-maintained dependencies.",
        "security_impact": "Medium",
        "effort": "Medium",
        "policy_relevance": "CISA Secure Software",
    },
    {
        "id": "remove-unmaintained",
        "title": "Remove unused or unmaintained packages",
        "description": "Identify dependencies that are no longer maintained or unused; replace or remove them.",
        "security_impact": "High",
        "effort": "Medium",
        "policy_relevance": "NIST SSDF, CISA",
    },
    {
        "id": "pin-versions",
        "title": "Pin versions where feasible",
        "description": "Prefer exact or narrow version ranges in declaration files to improve reproducibility and auditability.",
        "security_impact": "Medium",
        "effort": "Low",
        "policy_relevance": "EO 14028",
    },
    {
        "id": "automated-updates",
        "title": "Introduce automated dependency updates",
        "description": "Use Dependabot, Renovate, or similar to open PRs for dependency updates; run Chifleton in CI on those PRs.",
        "security_impact": "High",
        "effort": "Medium",
        "policy_relevance": "NIST SSDF RV.1, CISA",
    },
    {
        "id": "sbom-ci",
        "title": "Add SBOM generation to CI/CD",
        "description": "Generate a Software Bill of Materials (CycloneDX or SPDX) in CI and retain for release artifacts.",
        "security_impact": "High",
        "effort": "Medium",
        "policy_relevance": "EO 14028 Sec. 4(c)",
    },
]


def get_improvement_recommendations() -> list[dict[str, Any]]:
    """Return list of project-level improvement recommendations (for reports when --include-guidance)."""
    return list(RECOMMENDATIONS)
