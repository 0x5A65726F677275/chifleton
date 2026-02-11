"""Remediation intelligence: fix availability, recommended action, priority, risk."""

from typing import Any


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into comparable tuple (integers)."""
    if not version or not isinstance(version, str):
        return (0,)
    s = version.strip()
    for i, c in enumerate(s):
        if c.isdigit() or c == ".":
            continue
        s = s[:i]
        break
    parts = s.split(".")
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out) if out else (0,)


def _version_gte(version_a: str, version_b: str) -> bool:
    """True if version_a >= version_b."""
    ta = _parse_version(version_a)
    tb = _parse_version(version_b)
    max_len = max(len(ta), len(tb))
    ta = ta + (0,) * (max_len - len(ta))
    tb = tb + (0,) * (max_len - len(tb))
    return ta >= tb


def _fixed_versions_from_vuln(vuln: dict[str, Any]) -> list[str]:
    """Extract list of fixed versions from OSV vulnerability (affected ranges or database_specific.fixed_in)."""
    fixed: list[str] = []
    for aff in vuln.get("affected") or []:
        if not isinstance(aff, dict):
            continue
        for rng in aff.get("ranges") or []:
            if not isinstance(rng, dict):
                continue
            for ev in rng.get("events") or []:
                if isinstance(ev, dict) and isinstance(ev.get("fixed"), str):
                    fixed.append(ev["fixed"])
    ds = vuln.get("database_specific") or {}
    fi = ds.get("fixed_in")
    if isinstance(fi, list):
        fixed.extend(f for f in fi if isinstance(f, str))
    elif isinstance(fi, str):
        fixed.append(fi)
    return list(dict.fromkeys(fixed))


def is_fix_available(vuln: dict[str, Any]) -> bool:
    """True if OSV indicates a fixed version exists."""
    return len(_fixed_versions_from_vuln(vuln)) > 0


def recommended_action(vuln: dict[str, Any], current_version: str) -> str:
    """
    Human-readable recommended action: upgrade, replace, remove, or check references.
    """
    fixed_list = _fixed_versions_from_vuln(vuln)
    if fixed_list:
        if len(fixed_list) == 1:
            return f"Upgrade to {fixed_list[0]}"
        return "Upgrade to one of: " + ", ".join(fixed_list[:5]) + (f" (+{len(fixed_list)-5} more)" if len(fixed_list) > 5 else "")
    return "Check references for upgrade or mitigation guidance."


def remediation_risk(vuln: dict[str, Any], current_version: str) -> str:
    """
    Heuristic: Low (patch/minor), Medium/High (major), Unknown.
    """
    fixed_list = _fixed_versions_from_vuln(vuln)
    if not current_version or current_version == "-" or not fixed_list:
        return "Unknown"
    curr = _parse_version(current_version)
    for f in fixed_list:
        fv = _parse_version(f)
        if len(curr) >= 1 and len(fv) >= 1 and curr[0] != fv[0]:
            return "High"  # major version bump
        if len(curr) >= 2 and len(fv) >= 2 and (curr[0], curr[1]) != (fv[0], fv[1]):
            return "Medium"  # minor
    return "Low"


def priority_from_severity(severity: str) -> str:
    """
    Map severity to priority: Critical/High -> Immediate, Medium -> Planned, Low/Unknown -> Monitor.
    """
    s = (severity or "").strip().upper()
    if s in ("CRITICAL", "HIGH"):
        return "Immediate"
    if s in ("MEDIUM", "MODERATE"):
        return "Planned"
    return "Monitor"


def enrich_vuln_remediation(
    vuln: dict[str, Any],
    pkg_version: str,
    severity_label: str,
) -> dict[str, Any]:
    """
    Add remediation intelligence fields to a vulnerability dict.
    Returns additions: fix_available, recommended_action, remediation_risk, priority.
    """
    fix_available = is_fix_available(vuln)
    return {
        "fix_available": fix_available,
        "recommended_action": recommended_action(vuln, pkg_version or "-"),
        "remediation_risk": remediation_risk(vuln, pkg_version or "-"),
        "priority": priority_from_severity(severity_label),
    }
