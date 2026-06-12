# Milestone 6: LLM-Guided Instructions

*Introduce a Supervisor LLM to dynamically generate reusable, high-level guidelines for solver LLMs, with auto-invalidation after `n` consecutive failures.*

## Phases

### Phase 10: Supervisor LLM Integration & Guideline Generation
- Define the Supervisor LLM configuration and prompt structure.
- Implement the guideline generation logic to analyze challenge types and output general strategy text.

### Phase 11: Guideline Caching & Invalidation Logic
- Implement a local caching mechanism (e.g., JSON file) to store and retrieve generated guidelines by challenge type.
- Add failure tracking logic inside the challenge loop to monitor consecutive failures.
- Implement cache invalidation and regeneration fallback when failures exceed `n`.
