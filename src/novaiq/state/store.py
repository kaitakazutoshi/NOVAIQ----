"""SQLite-backed state to avoid posting the same paper twice."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import List, Tuple

from ..config import STATE_DB_PATH


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(STATE_DB_PATH)
    with closing(conn.cursor()) as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS posted (
                paper_key TEXT PRIMARY KEY,
                title TEXT,
                wp_post_id INTEGER,
                template_id TEXT,
                created_at TEXT
            )"""
        )
        conn.commit()
    return conn


def _key(source: str, source_id: str, doi: str) -> str:
    return (doi or f"{source}:{source_id}").lower().strip()


def already_posted(source: str, source_id: str, doi: str = "") -> bool:
    with closing(_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT 1 FROM posted WHERE paper_key = ?", (_key(source, source_id, doi),))
        return cur.fetchone() is not None


def mark_posted(
    source: str, source_id: str, doi: str, title: str, wp_post_id: int | None, template_id: str
) -> None:
    with closing(_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT OR REPLACE INTO posted VALUES (?, ?, ?, ?, ?)",
            (
                _key(source, source_id, doi),
                title,
                wp_post_id,
                template_id,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def recent_posts(limit: int = 20) -> List[Tuple[str, int, str, str]]:
    with closing(_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT title, wp_post_id, template_id, created_at FROM posted "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()
