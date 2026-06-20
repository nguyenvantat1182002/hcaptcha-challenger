# hCaptcha Challenger API

## What This Is

A Flask-based API that exposes the core capabilities of the `hcaptcha-challenger` agent as a web service. It receives images and challenge prompts, processes them using the internal LLM agent, and returns the bounding box coordinates for clicks. This allows other applications to easily bypass hCaptcha challenges by communicating with this centralized API.

## Core Value

Expose the multimodal LLM solving capabilities as a simple HTTP API (via Flask), decoupled from the browser automation lifecycle.

## Requirements

### Validated

- ✓ The underlying `hcaptcha-challenger` package can process hCaptcha images using an LLM.

### Active

- [ ] Build a Flask API application to wrap the hCaptcha solver agent.
- [ ] API endpoint must accept image payloads and a challenge prompt (text).
- [ ] API must return click coordinates derived from the LLM.
- [ ] No authentication is required for this API (local/internal usage).

### Out of Scope

- [ ] End-to-end browser automation within the API itself (API only handles the image processing/solving logic).
- [ ] Complex authentication (OAuth, JWT, API Keys).
- [ ] Integration with FastAPI (since Flask was explicitly chosen).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Use Flask** | User preference over the existing optional FastAPI configuration. | Pending |
| **Input/Output format** | Receive image + prompt, return coordinates. Matches the raw LLM agent capabilities. | Pending |

## Current State (v1.0)
- Flask API base established with Waitress (Windows) / Gunicorn (Linux).
- `POST /solve` endpoint successfully wrapped `hcaptcha-challenger` tools.
- Supports image payload (base64) and text prompt payload.
- Returns proper array format coordinates.
- Supports dynamic `LLM_TIMEOUT` overrides per request, fully tested.

## Next Milestone Goals
- Define requirements for v1.1.

---
*Last updated: 2026-06-20 after v1.0 milestone completion*
