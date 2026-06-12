# Milestone 6 Requirements: LLM-Guided Instructions

## Context
Currently, the system relies on static, hard-coded instructions (`point.md`, `path.md`, `binary.md`) to guide the solver LLMs. As challenges evolve, static prompts might not be enough to capture the necessary abstraction required for specific types of tasks. The user wants to introduce a "Supervisor LLM" that can dynamically generate general, reusable instructions (guidelines) for the solver LLMs based on the current challenge.

## Business Requirements
- [x] 1. **Supervisor LLM Integration:**
   - Allow configuration of a Supervisor LLM model specifically dedicated to analyzing a challenge and generating guidance.
- [x] 2. **Dynamic Guidelines Generation:**
   - The Supervisor LLM will observe the challenge prompt and optionally the image to generate general, high-level guidelines for how the solver LLM should approach it.
   - The guidelines must be general enough to apply to subsequent challenges of the same type, rather than being overly detailed for one specific image.
- [x] 3. **Guideline Caching & Reuse:**
   - Generated guidelines must be saved to a local file/cache.
   - When a new challenge arrives, the system should first check if a valid cached guideline exists for that challenge type before invoking the Supervisor LLM.
- [x] 4. **Adaptive Invalidation (Retry Threshold):**
   - Track consecutive failures for a specific challenge type.
   - If the agent fails `n` consecutive times using the current cached guideline, the system must invalidate the cache and invoke the Supervisor LLM to generate a fresh, alternative guideline.

## Technical Constraints
- [x] Changes must seamlessly integrate with the existing `ChallengeRouter` or `RoboticArm` flow.
- [x] Ensure the prompt generation respects the `0-1000` coordinate space rules established in Milestone 5 by either injecting them independently or ensuring the supervisor LLM includes them.
- [x] `n` (failure threshold) should be configurable.

## Verification
- [x] Unit/Integration tests or end-to-end logs demonstrating the supervisor LLM generating a guide.
- [x] Logs demonstrating the system reusing the cached guide for subsequent attempts.
- [x] Logs demonstrating cache invalidation and regeneration after `n` consecutive failures.
