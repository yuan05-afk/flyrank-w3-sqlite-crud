"""FlyRank W3 · A2 — Stage 0: create SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI

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
