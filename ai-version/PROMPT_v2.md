# AI rematch — prompt v2 (improved)

Migrate a FastAPI Task CRUD API from an in-memory list to SQLite using Python's sqlite3.

Hard rules:
1. File tasks.db beside the app; create automatically if missing.
2. Table tasks: id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0.
3. On startup: CREATE TABLE IF NOT EXISTS, then SELECT COUNT(*) — INSERT three seed rows ONLY when count is 0. Never re-seed on restart.
4. Every SQL statement must use ? placeholders — never f-strings or string concatenation for values.
5. Endpoints (same behaviour as Assignment 1):
   - GET / → name/version/endpoints JSON
   - GET /health → {"status":"ok"}
   - GET /tasks → all rows
   - GET /tasks/{id} → 200 or 404 {"error":"Task not found"} (top-level error key, not detail)
   - POST /tasks {"title"} → 201 with DB-assigned id, done=false; empty/missing title → 400 {"error":"..."}
   - PUT /tasks/{id} title and/or done → 200; empty body → 400; missing id → 404
   - DELETE /tasks/{id} → 204 empty body or 404
6. Do not invent ORMs, auth, or extra columns unless asked.
7. Quarantine output under ai-version/main_v2.py
