# Phase 2: Core Agent Context

## Decisions

1. **Async Architecture**: The OpenRouter Agent will be fully asynchronous. It will use `AsyncOpenAI` for the API client, `asyncio` for execution, and `AsyncIOEventEmitter` from `pyee` for event hooks. This perfectly aligns with the project's existing asynchronous nature (`pytest-asyncio`).
2. **Conversation History Management**: 
   - *Rationale*: The original OpenRouter tutorial uses a stateful agent (maintaining a `self.messages` list) to allow continuous, multi-turn conversations without the caller having to pass the whole history each time.
   - *Decision*: We will implement a stateful agent by default (matching the tutorial's `self.messages = []`), but will also provide a method to overwrite or pass history externally if `hcaptcha-challenger` needs it to be stateless in certain workflows.
3. **Tools/Function Calling Parsing**: We will leverage the `openai` Python SDK's built-in capability to parse Pydantic models directly into JSON schemas, which is the most modern, clean, and bug-free approach.

## Next Steps
This context locks in the asynchronous, event-driven, and Pydantic-native approach for Phase 2 implementation.
