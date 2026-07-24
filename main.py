"""
FlyRank Internship · Backend Track · W3 A2
Task API with SQLite persistence — same CRUD doors, durable storage.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from database import (
    DB_PATH,
    create_task_sql,
    delete_task_sql,
    fetch_task,
    get_connection,
    init_db,
    list_tasks_sql,
    row_to_task,
    stats_sql,
    update_task_sql,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Task API",
    version="2.0.0",
    description=(
        "FlyRank W3 · A2 — same task CRUD as Week 2, now backed by **SQLite** (`tasks.db`). "
        "Restart the server: your data is still there. Interactive docs: **/docs**."
    ),
    lifespan=lifespan,
    contact={"name": "FlyRank Backend Intern"},
    license_info={"name": "MIT"},
)


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool
    created_at: str | None = None
    updated_at: str | None = None


class ErrorOut(BaseModel):
    error: str


class StatsOut(BaseModel):
    total: int
    done: int
    open: int


class ApiInfo(BaseModel):
    name: str
    version: str
    storage: str
    database: str
    endpoints: list[str]


class HealthOut(BaseModel):
    status: str
    database: str


@app.get(
    "/",
    response_model=ApiInfo,
    tags=["meta"],
    summary="API front door",
    description="Describes the API. Storage is SQLite — endpoints match Assignment 1.",
)
def root() -> dict[str, Any]:
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": "sqlite",
        "database": DB_PATH.name,
        "endpoints": ["/tasks", "/stats", "/health", "/docs"],
    }


@app.get(
    "/health",
    response_model=HealthOut,
    tags=["meta"],
    summary="Liveness check",
)
def health() -> dict[str, str]:
    return {"status": "ok", "database": DB_PATH.name}


@app.get(
    "/stats",
    response_model=StatsOut,
    tags=["extras"],
    summary="Task counts (SQL)",
    description="Computed with SELECT COUNT(*) in SQLite — not a Python loop.",
)
def stats() -> dict[str, int]:
    return stats_sql()


@app.get(
    "/tasks",
    response_model=list[TaskOut],
    tags=["tasks"],
    summary="List tasks",
    description=(
        "SELECT from tasks.db. Optional: done filter, LIKE search, alphabetical sort."
    ),
)
def list_tasks(
    done: bool | None = Query(None, description="Filter by done flag (SQL WHERE)."),
    search: str | None = Query(None, description="Substring match via SQL LIKE."),
    sort: bool = Query(False, description="If true, ORDER BY title."),
) -> list[dict[str, Any]]:
    return list_tasks_sql(done=done, search=search, sort=sort)


@app.get(
    "/tasks/{task_id}",
    response_model=TaskOut,
    tags=["tasks"],
    summary="Get one task",
    responses={404: {"model": ErrorOut}},
)
def get_task(task_id: int) -> dict[str, Any] | JSONResponse:
    with get_connection() as conn:
        row = fetch_task(conn, task_id)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return row_to_task(row)


@app.post(
    "/tasks",
    response_model=TaskOut,
    status_code=201,
    tags=["tasks"],
    summary="Create a task",
    responses={400: {"model": ErrorOut}},
)
async def create_task(request: Request) -> dict[str, Any] | JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Request body must be JSON"})

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=400,
            content={"error": "Request body must be a JSON object"},
        )

    title = body.get("title")
    if title is None or not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and must be a non-empty string"},
        )

    return create_task_sql(title.strip())


@app.put(
    "/tasks/{task_id}",
    response_model=TaskOut,
    tags=["tasks"],
    summary="Update a task",
    responses={400: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
async def update_task(task_id: int, request: Request) -> dict[str, Any] | JSONResponse:
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
        done = int(row["done"])

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

    updated = update_task_sql(task_id, title, done)
    if updated is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return updated


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    tags=["tasks"],
    summary="Delete a task",
    response_class=Response,
)
def delete_task(task_id: int):
    if not delete_task_sql(task_id):
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return Response(status_code=204)
