# Phase 10 Context: Supervisor LLM Integration & Guideline Generation

## Decisions Made

1. **Supervisor Configuration:**
   - The model name will be configured via `SUPERVISOR_MODEL` in the `.env` file (e.g., `SUPERVISOR_MODEL=google/gemini-2.5-pro`).
   - It will reuse the same Provider and API Key configured for the solver LLMs (e.g., OpenRouter or Google GenAI), avoiding the need to configure separate credentials.

2. **Guideline Generation Strategy:**
   - To ensure the Supervisor produces an effective but "general" guideline, we will provide it with:
     - The `challenge_prompt` (e.g., "Find the dog").
     - The visual crop of the *first* challenge image to give it contextual understanding of what the objects look like in this specific hCaptcha context.
   - The prompt for the Supervisor must explicitly ask it to output a *general strategy* that is not overfitted to the specific layout of the first image (so it remains valid for subsequent iterations).

3. **Injection Method (Enforcing Obedience):**
   - The generated guideline must be injected into a section of the prompt where the Solver LLMs are "forced to obey". 
   - This will be implemented by prepending or appending the guideline to the core `auxiliary_information` or `system_prompt` (potentially wrapped in an authoritative markdown block like `## SUPERVISOR GUIDANCE`), overriding normal behavior.

## Scope Limits
- Phase 10 handles **only** the integration of the Supervisor LLM and the prompt/logic to generate the string of instructions.
- Tracking the `n` failures and caching to a JSON file will be implemented in Phase 11. For Phase 10, we will assume a generic function `get_or_generate_guideline(prompt, image)` exists and returns a string.
