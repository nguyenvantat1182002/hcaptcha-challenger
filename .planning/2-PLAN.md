# Phase 2: Core Agent Implementation Plan

## Objective
Implement the asynchronous `Agent` core class utilizing `AsyncOpenAI` and `pyee.AsyncIOEventEmitter` to support event-driven, multi-turn conversations via OpenRouter API.

## Context
See `.planning/2-CONTEXT.md` for architectural decisions (Async flow, Pydantic Schema parsing).

## Steps
1. **Implement `Agent` Class**:
   - Create `src/hcaptcha_challenger/tools/internal/providers/openrouter/agent.py`.
   - Inherit from `pyee.AsyncIOEventEmitter`.
   - Initialize `AsyncOpenAI(base_url="https://openrouter.ai/api/v1")` using the provided API key.
   - Maintain `self.messages` state for conversation history.
2. **Implement Streaming Logic**:
   - Create the `async def send(self, content: str, tools: list = None)` method.
   - Send messages to OpenRouter with `stream=True`.
   - Process the async generator `chunk by chunk`.
   - Emit events using `self.emit()`:
     - `stream:start`
     - `stream:delta` (with new text chunk)
     - `tool:call` (when a function is requested by the LLM)
     - `stream:end`
3. **History Management**:
   - Create methods `get_messages()`, `clear_history()`, and `set_instructions()` for system prompt overrides.

## Verification
- Validate the syntax using Python linters (e.g., `ruff`).
- Ensure no synchronous blocking operations exist in the `send` method.
