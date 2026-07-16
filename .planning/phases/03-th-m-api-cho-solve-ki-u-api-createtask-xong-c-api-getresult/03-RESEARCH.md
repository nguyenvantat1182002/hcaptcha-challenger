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

## Deprecating `/solve`
- **Scope Analysis**: A search for `"/solve"` across the codebase reveals that the synchronous `/solve` endpoint is currently referenced in:
  - `src/hcaptcha_challenger/server/app.py`: The actual route definition.
  - `test_solve.py`: A manual test script hitting `http://127.0.0.1:8000/solve`.
  - `AGENT_SKILL.md`: The integration manual used by external agents (both Python and Node.js examples).
- **Action Required**: Removing `/solve` from `app.py` is straightforward, but it necessitates updating both the test script (`test_solve.py`) and the public documentation (`AGENT_SKILL.md`) to ensure clients adopt the new two-step `/createTask` -> `/getTaskResult` flow.

## Validation Architecture
- Define a dictionary `tasks = {}` at the module level.
- Generate a UUID `taskId` for each request.
- Run `SolverService` in the background thread. Once completed, update the `tasks[taskId]` with `status="ready"` and the result.
- Implement lazy cleanup: during `createTask` or `getTaskResult`, purge tasks that have exceeded their `timeout`.
