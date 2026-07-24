# Stage 4 — SQL explored by hand


Opened 	asks.db (same file the API uses) and ran:

## SELECT * FROM tasks;

Returned (SELECT * FROM tasks):

| id | title | done |
| --- | --- | --- |
| 1 | Draft SEO report outline for client onboarding | 0 |
| 2 | Review Crawl API response schemas | 1 |
| 3 | Ship Week 3 SQLite persistence checkpoints | 0 |

## SELECT * FROM tasks WHERE done = 1;

Returned (completed only):

| id | title | done |
| --- | --- | --- |
| 2 | Review Crawl API response schemas | 1 |

## SELECT COUNT(*) AS n FROM tasks;

Returned (count):

| n |
| --- |
| 3 |

## UPDATE tasks SET done = 1;

Marked every row completed. Before: 3 tasks; after: 3 rows with done=1.
Calling GET /tasks then shows the same change instantly — one file, one source of truth.
