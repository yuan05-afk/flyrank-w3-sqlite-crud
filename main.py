"""FlyRank W3 · A2 — Stage 3: update and delete with SQL."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

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


def fetch_task(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()


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
        row = fetch_task(conn, task_id)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return row_to_task(row)


@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Request body must be JSON"})

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "Request body must be a JSON object"})

    title = body.get("title")
    if title is None or not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and must be a non-empty string"},
        )

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title.strip(), 0),
        )
        conn.commit()
        row = fetch_task(conn, cur.lastrowid)
    return row_to_task(row)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Request body must be JSON"})

    if not isinstance(body, dict) or not body:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body must include title and/or done"},
        )

    if "title" not in body and "done" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body must include title and/or done"},
        )

    with get_connection() as conn:
        row = fetch_task(conn, task_id)
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})

        title = row["title"]
        done = row["done"]

        if "title" in body:
            new_title = body["title"]
            if not isinstance(new_title, str) or not new_title.strip():
                return JSONResponse(
                    status_code=400,
                    content={"error": "title must be a non-empty string"},
                )
            title = new_title.strip()

        if "done" in body:
            new_done = body["done"]
            if not isinstance(new_done, bool):
                return JSONResponse(
                    status_code=400,
                    content={"error": "done must be a boolean"},
                )
            done = 1 if new_done else 0

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, done, task_id),
        )
        conn.commit()
        row = fetch_task(conn, task_id)

    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_connection() as conn:
        row = fetch_task(conn, task_id)
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return Response(status_code=204)
