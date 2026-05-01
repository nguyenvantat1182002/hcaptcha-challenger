# Codebase Concerns

**Analysis Date:** 2025-05-14

## Tech Debt

**Project Structure:**
- Issue: Log files are being stored directly within the source tree.
- Files: `src/hcaptcha_challenger/logs/`
- Impact: Pollutes the source directory and makes packaging/deployment more complex.
- Fix approach: Move logging to a dedicated root-level directory or system temp directory, configurable via environment variables.

**Stale Code:**
- Issue: An `archive/` directory exists in the root, containing what looks like old versions of the codebase.
- Files: `archive/`
- Impact: Increases codebase size and confuses developers about the source of truth.
- Fix approach: Move archive contents to a separate branch or external storage and remove from the main branch.

**Compiled Artifacts:**
- Issue: `__pycache__` and `.pyc` files appearing in directory listings suggest they might be tracked or not properly ignored.
- Files: `src/hcaptcha_challenger/**/__pycache__`
- Impact: Noise in the repository and potential for stale bytecode issues.
- Fix approach: Ensure `.gitignore` properly excludes all `__pycache__` and bytecode files.

## Security Considerations

**LLM Provider Integration:**
- Risk: Usage of external LLM APIs (Gemini, OpenRouter) involves sending challenge data to third parties.
- Files: `src/hcaptcha_challenger/tools/internal/providers/gemini.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`
- Current mitigation: API keys are likely handled via environment variables (referenced in `examples/.env.example`).
- Recommendations: Implement strict data scrubbing if sensitive information might be present in challenges; ensure rate limiting to prevent cost spikes.

## Performance Bottlenecks

**Media Conversion:**
- Problem: Tests involve WebM to MP4 conversion which can be resource-intensive.
- Files: `src/hcaptcha_challenger/helper/webm_to_mp4.py`
- Cause: Calling external processes (likely ffmpeg) for transcoding.
- Improvement path: Optimize conversion parameters or avoid conversion if the downstream tools can handle WebM directly.

**Synchronous I/O in Agent:**
- Problem: The agent appears to handle mouse movements and robotic interactions which might be timing-sensitive.
- Files: `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/agent/mouse.py`
- Cause: Potential for blocking calls during interaction simulation.
- Improvement path: Audit for blocking I/O in critical paths and consider asynchronous execution for non-blocking tasks.

---

*Concerns audit: 2025-05-14*
