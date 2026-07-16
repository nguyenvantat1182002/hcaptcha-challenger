# Phase 3: Technical Research

## Background
We need to add a 2-step async API (`createTask` and `getTaskResult`) for solving hCaptcha. This prevents HTTP timeouts for clients calling the synchronous `/solve` endpoint, as remote LLM solvers can take a long time.

## Context Decisions
1. **Task Storage**: In-memory dictionary.
2. **Background Execution**: Use `asyncio` to run tasks in the background without external message brokers like Celery.
3. **Cleanup**: Support configurable timeout; automatically delete expired tasks.

## Codebase Analysis
- **`src/hcaptcha_challenger/server/app.py`**: Current entry point for Flask. The `/solve` endpoint reads the payload and calls `asyncio.run(solver.solve_challenge(...))`.
- **`src/hcaptcha_challenger/server/solve.py`**: `SolverService.solve_challenge` is fully asynchronous.

## Technical Feasibility & Risks
- **Risk (Event Loop Lifecycle)**: Standard Flask (WSGI) is synchronous. While Flask 2.0+ supports `async def` routes, it creates a new event loop per request (via `asyncio.run`). Any background `asyncio.create_task` spawned inside the route will be abruptly killed when the route returns and the loop closes.
- **Solution**: We must maintain a persistent, long-lived asyncio event loop in a background thread. When `/createTask` is called, we submit the coroutine to this background loop using `asyncio.run_coroutine_threadsafe()`.

## Validation Architecture
- Define a dictionary `tasks = {}` at the module level.
- Generate a UUID `taskId` for each request.
- Run `SolverService` in the background thread. Once completed, update the `tasks[taskId]` with `status="ready"` and the result.
- Implement lazy cleanup: during `createTask` or `getTaskResult`, purge tasks that have exceeded their `timeout`.
