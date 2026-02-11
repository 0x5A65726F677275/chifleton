"""OSV.dev API client for querying vulnerabilities."""

import requests
from typing import Any

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
ECOSYSTEM_PYPI = "PyPI"
ECOSYSTEM_NPM = "npm"
TIMEOUT = 30


def query_vulnerabilities(
    pkg: str,
    version: str | None,
    ecosystem: str = ECOSYSTEM_PYPI,
) -> dict[str, Any]:
    """
    Query OSV for vulnerabilities affecting the given package (and optional version).
    Returns the raw API response (with 'vulns' list or empty).
    ecosystem: "PyPI" for Python, "npm" for Node.js.
    """
    payload: dict[str, Any] = {
        "package": {"name": pkg, "ecosystem": ecosystem},
    }
    if version:
        payload["version"] = version

    try:
        resp = requests.post(OSV_QUERY_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except requests.RequestException as e:
        return {"_error": str(e), "vulns": []}


def get_vulns_from_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract vulns list from OSV response; handle errors and empty results."""
    if response.get("_error"):
        return []
    vulns = response.get("vulns")
    if vulns is None:
        return []
    return vulns if isinstance(vulns, list) else []
