# Codebase Concerns

**Analysis Date:** 2026-04-30

## Tech Debt

**Mixed async/sync tool contracts:**
- Issue: Base abstraction defines async invocation while concrete tool implementations are synchronous, creating ambiguous call contracts and type drift.
- Files: `src/hcaptcha_challenger/tools/internal/base.py`, `src/hcaptcha_challenger/tools/image_classifier/__init__.py`, `src/hcaptcha_challenger/tools/challenge_router/__init__.py`, `src/hcaptcha_challenger/tools/spatial/point.py`, `src/hcaptcha_challenger/tools/spatial/path.py`
- Impact: Integrators and tests can call tools with incompatible await semantics; static typing and runtime behavior diverge.
- Fix approach: Standardize one contract (sync or async) across `Reasoner` and all subclasses, then update tests and docs to match that single interface.

**Large orchestration classes with cross-cutting responsibilities:**
- Issue: Browser automation, screenshot capture, model invocation, retry logic, and click/drag execution are concentrated in large classes.
- Files: `src/hcaptcha_challenger/agent/robotic.py`, `src/hcaptcha_challenger/agent/challenger.py`
- Impact: Regression risk is high for routine changes; independent testing of decision logic vs browser side effects is difficult.
- Fix approach: Extract focused services (challenge parsing, interaction executor, capture pipeline, response watcher) and add unit tests at service boundaries.

**Legacy/placeholder command paths in CLI:**
- Issue: CLI includes not-yet-implemented paths and catches broad exceptions at top-level handlers.
- Files: `src/hcaptcha_challenger/cli/dataset.py`, `src/hcaptcha_challenger/cli/main.py`
- Impact: Operators receive generic failures; root-cause diagnostics and observability are weak.
- Fix approach: Replace placeholder routes with explicit `NotImplementedError` + actionable help text, and narrow exception handling to known failure classes.

## Known Bugs

**Constructor argument mismatch in tests and public usage patterns:**
- Symptoms: Tests instantiate tools with `gemini_api_key=...` while tool constructors accept `openrouter_api_key`.
- Files: `src/hcaptcha_challenger/tools/image_classifier/__init__.py`, `src/hcaptcha_challenger/tools/challenge_router/__init__.py`, `src/hcaptcha_challenger/tools/internal/base.py`, `tests/test_tools_image_classifier.py`, `tests/test_tools_challenge_classifier.py`, `tests/test_tools_spatial_point_reasoning.py`, `tests/test_tools_spatial_path_reasoning.py`, `tests/test_tools_spatial_bbox_reasoning.py`
- Trigger: Running tests or downstream code that follows existing test examples.
- Workaround: Pass `openrouter_api_key` explicitly or inject `provider=` to bypass default provider setup.

**Signal typing drift in challenge flow:**
- Symptoms: Solver path returns `None`/`False` in functions typed as `ChallengeSignal`, causing ambiguous downstream state.
- Files: `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/models.py`
- Trigger: Unknown challenge type or ignored challenge branch in `_solve_captcha()` / `wait_for_challenge()`.
- Workaround: Treat non-success outcomes as failure externally and guard against null-like returns.

## Security Considerations

**Remote skill update trust boundary:**
- Risk: Runtime downloads remote YAML/templates and writes directly into local cache without signature verification or pinning.
- Files: `src/hcaptcha_challenger/skills/manager.py`
- Current mitigation: Uses HTTPS and `yaml.safe_load`; optional feature behind `enable_skills_update`.
- Recommendations: Pin commit SHA/version manifests, add content hash verification, and enforce explicit allowlist for repositories/branches.

**Deserialization and browser-script execution on untrusted challenge payloads:**
- Risk: Network payload bytes are decoded via `msgpack.unpackb`, then transformed through `run_js`-driven flow.
- Files: `src/hcaptcha_challenger/agent/challenger.py`
- Current mitigation: Pydantic model validation (`CaptchaPayload`) and exception fallback.
- Recommendations: Add schema size limits, reject oversized packets, and instrument strict validation/error counters before queueing payloads.

## Performance Bottlenecks

**Repeated full-image upload and processing loops per crumb:**
- Problem: Each crumb captures screenshots, writes artifacts, uploads image content, and invokes remote model calls serially.
- Files: `src/hcaptcha_challenger/agent/robotic.py`, `src/hcaptcha_challenger/tools/internal/providers/gemini.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`
- Cause: Tight loop architecture with per-crumb synchronous remote inference and repeated file I/O.
- Improvement path: Batch or reuse immutable artifacts per round, add request timeout/backoff tuning, and profile image preprocessing vs network time.

**Heavy visualization and media conversion helpers on hot data paths:**
- Problem: Image/video helper modules include high-cost operations and disk writes with limited throttling.
- Files: `src/hcaptcha_challenger/helper/create_comparison_image.py`, `src/hcaptcha_challenger/helper/visualize_attention_points.py`, `src/hcaptcha_challenger/helper/webm_to_mp4.py`
- Cause: Bulk file traversal plus synchronous CPU-bound processing.
- Improvement path: Add bounded worker pools, streaming I/O where possible, and optional lightweight modes for CI/debug runs.

## Fragile Areas

**Dependence on private DrissionPage internals:**
- Files: `src/hcaptcha_challenger/agent/robotic.py`
- Why fragile: Uses internal/private attributes and methods (`_dr`, `_hold`, `_release`, `_run_cdp`) that can break on upstream minor updates.
- Safe modification: Isolate private API usage into a compatibility adapter module and gate with version checks + fallback paths.
- Test coverage: No deterministic unit tests validate this adapter behavior against mocked DrissionPage contracts.

**Queue/thread lifecycle coupling to browser listeners:**
- Files: `src/hcaptcha_challenger/agent/challenger.py`
- Why fragile: A daemon thread processes listener packets with no shutdown handshake or queue drain protocol.
- Safe modification: Introduce explicit lifecycle controls (start/stop/join), sentinel events, and time-bounded queue consumers.
- Test coverage: No tests assert thread safety, listener termination, or race conditions under empty/late packet scenarios.

## Scaling Limits

**Single-instance, local-state execution model:**
- Current capacity: Designed for one browser frame/session workflow with in-process queues and local filesystem cache.
- Limit: Throughput degrades when scaling concurrent challenge sessions due to serialized loop and shared process resources.
- Scaling path: Move challenge workers to process-level isolation, externalize state/cache, and enforce per-session concurrency controls.

**API-cost growth with linear challenge volume:**
- Current capacity: Cost tracking exists but inference remains per-challenge and per-crumb.
- Limit: Token and request cost grows roughly linearly with no adaptive throttling budget.
- Scaling path: Add model routing policy by challenge complexity and implement budget-aware fallback tiers in `src/hcaptcha_challenger/helper/cost_calculator.py` and solver orchestration.

## Dependencies at Risk

**Preview model identifiers in defaults/tests:**
- Risk: Preview model names can be deprecated or behavior-shift without strong compatibility guarantees.
- Impact: Runtime inference and tests can fail abruptly when model catalog changes.
- Migration plan: Centralize model capability discovery and pin stable model families in `src/hcaptcha_challenger/models.py` with fallback list resolution.

**Private API coupling for browser library:**
- Risk: DrissionPage internal API changes can break core interaction paths.
- Impact: Solver click/drag operations fail even when model outputs are valid.
- Migration plan: Introduce public-API-only adapter path and compatibility matrix tests for supported versions.

## Missing Critical Features

**Deterministic offline test harness for solver core:**
- Problem: Core solver behavior depends on live model APIs and browser state, but no local deterministic harness exists for critical flows.
- Blocks: Reliable regression testing for `_review_challenge_type`, `_solve_captcha`, and interaction sequencing.

**CI gating on active PR/push events:**
- Problem: Existing workflows are mostly manual dispatch and commented PR triggers.
- Blocks: Automated detection of interface regressions and dependency breakage before merge.

## Test Coverage Gaps

**Agent orchestration and concurrency are largely untested:**
- What's not tested: Queue handling, thread lifecycle, timeout signaling, and state transitions in challenge execution loop.
- Files: `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/agent/robotic.py`
- Risk: Race conditions and timeout regressions can ship undetected.
- Priority: High

**Provider abstraction and constructor compatibility:**
- What's not tested: Contract consistency for sync/async invocation and constructor keyword compatibility (`openrouter_api_key` vs `gemini_api_key`).
- Files: `src/hcaptcha_challenger/tools/internal/base.py`, `src/hcaptcha_challenger/tools/internal/providers/gemini.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`, `src/hcaptcha_challenger/tools/image_classifier/__init__.py`
- Risk: Breaking public API usage and intermittent runtime failures.
- Priority: High

**CI-safe unit tests are mixed with live API integration patterns:**
- What's not tested: Offline fallback behavior and deterministic logic without external API keys.
- Files: `tests/test_tools_common.py`, `tests/test_tools_challenge_classifier.py`, `tests/test_tools_image_classifier.py`, `tests/test_tools_spatial_point_reasoning.py`, `tests/test_tools_spatial_path_reasoning.py`
- Risk: Test suite reliability is environment-dependent and can mask real regressions.
- Priority: Medium

---

*Concerns audit: 2026-04-30*
