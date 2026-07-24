# AI rematch — prompt v1 (from memory)

Take my FastAPI in-memory task CRUD API and move storage to SQLite.

Use Python's built-in sqlite3 module. Database file: tasks.db next to the app.

On startup:
- create tasks table if missing with id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, done INTEGER 0/1
- seed exactly 3 example tasks only when the table is empty

Keep the same endpoints and behaviour:
- GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}
- POST missing/empty title → 400
- unknown id → 404 with {"error":"Task not found"}
- create → 201, delete success → 204 empty body
- use parameterized SQL with ? placeholders everywhere

Also keep GET / and GET /health. Put code in ai-version/.
