# Plan: 02-implement-solver-endpoint
*Goal: Build the POST endpoint to receive images and prompts and return LLM solver coordinates.*

<objective>
Implement a `/solve` POST endpoint in the Flask application that wraps the `hcaptcha-challenger` core tools. The endpoint will accept JSON containing a base64 image and a challenge prompt, route it to the correct AI reasoner (`ImageClassifier`, `SpatialPointReasoner`, or `SpatialPathReasoner`), and return a structured JSON response containing the solved coordinates. The AI tools will be initialized once at startup to minimize latency.
</objective>

<tasks>

1. **Implement Solver Service Logic (`src/hcaptcha_challenger/server/solve.py`)**
   - Create a `SolverService` class responsible for maintaining singletons of the AI tools.
   - Initialize `ChallengeRouter`, `ImageClassifier`, `SpatialPointReasoner`, and `SpatialPathReasoner` using `AgentConfig`.
   - Add a `solve_challenge(prompt: str, image_b64: str)` async method.
   - Decode the base64 string to a temporary image file on disk.
   - Run `ChallengeRouter` (or rely on prompt matching) to determine the `RequestType` or `ChallengeTypeEnum`.
   - Dispatch to the corresponding reasoner tool.
   - Format the tool's raw output (`ImageBinaryChallenge`, `ImageAreaSelectChallenge`, etc.) into a unified `[{"x": 10, "y": 20}]` structure.
   - Delete the temporary image file.

2. **Integrate into Flask API (`src/hcaptcha_challenger/server/app.py`)**
   - Add `POST /solve` route using Flask 3.0's async support (`async def solve()`).
   - Validate incoming JSON: must contain `prompt` and `image`.
   - Instantiate/access the global `SolverService`.
   - Await `solve_challenge(prompt, image)`.
   - Handle exceptions (e.g., base64 decoding errors, API request timeouts) and return appropriate HTTP status codes (400, 500).
   - Return standard JSON response: `{"success": true, "coordinates": [...]}`.

</tasks>

<files_modified>
- src/hcaptcha_challenger/server/app.py
- src/hcaptcha_challenger/server/solve.py
</files_modified>
