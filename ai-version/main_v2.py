"""
AI rematch v2 — improved prompt. Still quarantined; closer to the hand-built rules.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

DB_PATH = Path(__file__).resolve().parent / "tasks_v2.db"
SEED = [
    ("Learn SQLite", 0),
    ("Write parameterized queries", 0),
    ("Prove persistence", 1),
]

app = FastAPI(title="Task API")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
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
                SEED,
            )
        conn.commit()


init_db()


def as_task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [as_task(r) for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return as_task(row)


@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    body = await request.json()
    title = body.get("title") if isinstance(body, dict) else None
    if not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and must be a non-empty string"},
        )
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title.strip(), 0),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return as_task(row)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    body = await request.json()
    if not isinstance(body, dict) or not body:
        return JSONResponse(status_code=400, content={"error": "empty body"})
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})
        title = row["title"]
        done = row["done"]
        if "title" in body:
            if not isinstance(body["title"], str) or not body["title"].strip():
                return JSONResponse(status_code=400, content={"error": "invalid title"})
            title = body["title"].strip()
        if "done" in body:
            if not isinstance(body["done"], bool):
                return JSONResponse(status_code=400, content={"error": "invalid done"})
            done = 1 if body["done"] else 0
        if "title" not in body and "done" not in body:
            return JSONResponse(status_code=400, content={"error": "empty body"})
        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, done, task_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return as_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return Response(status_code=204)
