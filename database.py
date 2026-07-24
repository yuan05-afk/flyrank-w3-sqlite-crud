"""
FlyRank W3 · A2 — SQLite storage helpers.
Parameterized queries only. tasks.db is created and seeded on first run.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "tasks.db"

SEED_TASKS = [
    ("Draft SEO report outline for client onboarding", 0),
    ("Review Crawl API response schemas", 1),
    ("Ship Week 3 SQLite persistence checkpoints", 0),
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create schema, index, and seed three examples only when empty (one transaction)."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # Older DBs from early stages may lack timestamp columns — grow the schema gently.
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        if "created_at" not in cols:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"
            )
        if "updated_at" not in cols:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN updated_at TEXT NOT NULL DEFAULT (datetime('now'))"
            )

        # Index speeds title search (LIKE) — an index is a sorted lookup helper for a column.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks (title)"
        )

        count = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        if count == 0:
            # All-or-nothing seed: if one insert fails, none stick.
            with conn:
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)",
                    SEED_TASKS,
                )


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    task: dict[str, Any] = {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }
    keys = row.keys()
    if "created_at" in keys and row["created_at"] is not None:
        task["created_at"] = row["created_at"]
    if "updated_at" in keys and row["updated_at"] is not None:
        task["updated_at"] = row["updated_at"]
    return task


def fetch_task(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()


def list_tasks_sql(
    *,
    done: bool | None = None,
    search: str | None = None,
    sort: bool = False,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if done is not None:
        clauses.append("done = ?")
        params.append(1 if done else 0)

    if search is not None and search.strip():
        clauses.append("title LIKE ?")
        params.append(f"%{search.strip()}%")

    sql = "SELECT * FROM tasks"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    if sort:
        sql += " ORDER BY title COLLATE NOCASE"
    else:
        sql += " ORDER BY id"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_task(r) for r in rows]


def stats_sql() -> dict[str, int]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        done = conn.execute(
            "SELECT COUNT(*) AS c FROM tasks WHERE done = ?",
            (1,),
        ).fetchone()["c"]
    return {"total": total, "done": done, "open": total - done}


def create_task_sql(title: str) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title, 0),
        )
        conn.commit()
        row = fetch_task(conn, cur.lastrowid)
    assert row is not None
    return row_to_task(row)


def update_task_sql(task_id: int, title: str, done: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = fetch_task(conn, task_id)
        if row is None:
            return None
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, done = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (title, done, task_id),
        )
        conn.commit()
        row = fetch_task(conn, task_id)
    assert row is not None
    return row_to_task(row)


def delete_task_sql(task_id: int) -> bool:
    with get_connection() as conn:
        row = fetch_task(conn, task_id)
        if row is None:
            return False
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return True
