"""Local SQLite cache for OSV API responses."""

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path.home() / ".chifleton"
CACHE_DB = "osv_cache.db"
TABLE = "osv_cache_v2"  # v2: ecosystem in PK for multi-ecosystem support


def _db_path() -> Path:
    DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CACHE_DIR / CACHE_DB


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def init_cache() -> None:
    """Create the cache table if it does not exist. Includes ecosystem for multi-ecosystem support."""
    conn = _get_conn()
    try:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                ecosystem TEXT NOT NULL DEFAULT 'PyPI',
                pkg TEXT NOT NULL,
                version TEXT,
                response_json TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (ecosystem, pkg, version)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_cached(pkg: str, version: str | None, ecosystem: str = "PyPI") -> dict[str, Any] | None:
    """
    Look up cached OSV response for (ecosystem, pkg, version).
    version is stored as empty string when None for consistency.
    """
    init_cache()
    conn = _get_conn()
    try:
        v = version if version is not None else ""
        row = conn.execute(
            f"SELECT response_json FROM {TABLE} WHERE ecosystem = ? AND pkg = ? AND version = ?",
            (ecosystem, pkg, v),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["response_json"])
    finally:
        conn.close()


def set_cached(
    pkg: str, version: str | None, response: dict[str, Any], ecosystem: str = "PyPI"
) -> None:
    """Store OSV response in cache."""
    init_cache()
    conn = _get_conn()
    try:
        v = version if version is not None else ""
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {TABLE} (ecosystem, pkg, version, response_json, fetched_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (ecosystem, pkg, v, json.dumps(response)),
        )
        conn.commit()
    finally:
        conn.close()
