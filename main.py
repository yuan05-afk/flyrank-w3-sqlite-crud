"""FlyRank W3 · A2 — Stage 1: database read endpoints."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                SEED_TASKS,
            )
        conn.commit()


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


app = FastAPI(title="Task API", version="2.0.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": "sqlite",
        "database": "tasks.db",
        "endpoints": ["/tasks"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "database": DB_PATH.name}


@app.get("/tasks")
def list_tasks():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [row_to_task(r) for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return row_to_task(row)
