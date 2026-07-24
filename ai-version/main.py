"""
AI rematch v1 — quarantined. Intentionally shows common AI migration slips.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
import sqlite3

app = FastAPI()
DB = "tasks.db"


def db():
    return sqlite3.connect(DB)


def setup():
    conn = db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, done INTEGER)"
    )
    # BUG for rematch: seeds every startup without counting first
    conn.execute("INSERT INTO tasks (title, done) VALUES ('Task A', 0)")
    conn.execute("INSERT INTO tasks (title, done) VALUES ('Task B', 0)")
    conn.execute("INSERT INTO tasks (title, done) VALUES ('Task C', 1)")
    conn.commit()
    conn.close()


setup()


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    conn = db()
    rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": bool(r[2])} for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = db()
    # unsafe-ish pattern the rematch critiques: f-string SQL
    row = conn.execute(f"SELECT id, title, done FROM tasks WHERE id = {task_id}").fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, detail="Task not found")
    return {"id": row[0], "title": row[1], "done": bool(row[2])}


@app.post("/tasks", status_code=201)
async def create(request: Request):
    body = await request.json()
    title = body.get("title", "")
    if not title:
        raise HTTPException(400, detail="title required")
    conn = db()
    cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return {"id": tid, "title": title, "done": False}


@app.put("/tasks/{task_id}")
async def update(task_id: int, request: Request):
    body = await request.json()
    conn = db()
    row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, detail="not found")
    title = body.get("title")
    done = body.get("done")
    if title is not None:
        conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
    if done is not None:
        conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (1 if done else 0, task_id))
    conn.commit()
    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    conn.close()
    return {"id": row[0], "title": row[1], "done": bool(row[2])}


@app.delete("/tasks/{task_id}", status_code=204)
def delete(task_id: int):
    conn = db()
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, detail="not found")
    return Response(status_code=204)
