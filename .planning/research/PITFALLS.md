# Domain Pitfalls

**Domain:** Cursor movement algorithm migration (legacy human-like -> HumanCursor-style in browser automation)
**Researched:** 2026-04-30
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

### Pitfall 1: Swapping motion math without parity baselines

**What goes wrong:**
The team replaces the cursor path generator, but solver success drops because movement timing/event cadence no longer matches production expectations.

**Why it happens:**
Migration is treated as "implementation detail" and not as a measurable behavior contract (path shape, move duration, event count, click latency, target hit rate).

**How to avoid:**
Before replacing logic, lock a baseline from current production runs:
- movement distribution metrics (distance, duration, velocity variance, overshoot frequency)
- DOM event metrics (`mousemove` count per action, pre-click hover delay)
- outcome metrics (challenge completion rate, retry rate, timeout rate)
Gate rollout on "no regression" thresholds.

**Warning signs:**
- More "missed click" or "re-click" behavior in challenge flow
- Increased timeout/retry rate in `robotic` execution
- Telemetry shows lower `mousemove` counts per interaction after migration

**Phase to address:**
Phase 1 - Baseline capture and quantitative parity benchmarks.

---

### Pitfall 2: Relying on framework-native interpolation as "human-like"

**What goes wrong:**
Migration uses built-in mouse interpolation (`steps`) and assumes that is sufficient; resulting movement is still overly linear/mechanical.

**Why it happens:**
`mouse.move()` interpolation is easy and appears smooth visually, but does not automatically model realistic acceleration/deceleration, jitter, overshoot, and correction behavior.

**How to avoid:**
Implement an explicit movement profile layer:
- path generation (Bezier/curved path)
- timing profile (non-uniform delays, not fixed intervals)
- optional overshoot + settle for long moves
- bounded micro-jitter and hover dwell before click
Keep this in one adapter/service so orchestration can switch profiles safely.

**Warning signs:**
- Cursor traces look smooth but too "perfect"
- Movement duration tightly correlated only to distance with little variance
- Event intervals nearly constant across runs

**Phase to address:**
Phase 2 - HumanCursor-style adapter and movement profile implementation.

---

### Pitfall 3: Breaking event semantics during click/hover migration

**What goes wrong:**
Cursor reaches target but expected event sequence differs, causing subtle interaction failures in hCaptcha widgets.

**Why it happens:**
Developers focus on final coordinates, not full interaction semantics (`mousemove` cadence, hover before click, down/up timing, scroll interactions).

**How to avoid:**
Define an interaction contract test suite:
- move -> hover dwell -> down -> up -> click
- drag/drop and scroll path behaviors
- assertions on event sequence/order for critical widget actions
Run contract tests in CI against supported browser backends.

**Warning signs:**
- Flaky widget interaction despite "correct" coordinates
- Hover-triggered UI states not activating reliably
- More nondeterministic failures in end-to-end tests

**Phase to address:**
Phase 3 - Interaction contract tests and cross-browser behavior verification.

---

### Pitfall 4: Coordinate drift under dynamic layout and viewport changes

**What goes wrong:**
HumanCursor-style movement targets stale coordinates and misses due to layout shifts, frame changes, scroll changes, or sticky overlays.

**Why it happens:**
Algorithm migration is done independently from target acquisition and revalidation logic.

**How to avoid:**
Use "locate-then-move" with pre-click validation:
- recompute element box immediately before movement execution
- revalidate visibility/intersection after scroll
- clamp to viewport and replan path when target moves
- fail fast with retry strategy on stale geometry

**Warning signs:**
- Clicks land near element edges or under overlays
- Failures spike on responsive pages/slow networks
- Retries succeed without algorithm changes (indicates stale target state)

**Phase to address:**
Phase 2 - Movement adapter integration with robust target revalidation.

---

### Pitfall 5: Ignoring existing fragile boundaries in orchestration layer

**What goes wrong:**
Cursor migration introduces regressions in already fragile classes (`robotic`/`challenger`) and private browser APIs.

**Why it happens:**
New movement logic is embedded directly into large cross-cutting classes instead of isolated behind an adapter boundary.

**How to avoid:**
Refactor before deep migration:
- isolate browser mouse primitives behind a compatibility adapter
- keep movement engine pure/testable (no direct page/frame side effects)
- add thin orchestration hooks rather than rewriting challenge lifecycle code

**Warning signs:**
- Large diff in `agent/robotic.py` touching unrelated logic
- Increased dependency on private browser internals during migration
- Bug fixes require editing multiple orchestration hotspots

**Phase to address:**
Phase 0 - Refactor safety boundaries (adapter extraction) before algorithm swap.

---

### Pitfall 6: Throughput collapse from realistic movement everywhere

**What goes wrong:**
Automation becomes "more human" but total run time/cost increases enough to hurt production throughput.

**Why it happens:**
Human-like movement is applied to every minor interaction instead of high-risk interactions only.

**How to avoid:**
Adopt selective realism policy:
- high-fidelity movement for challenge-critical actions
- lightweight movement for low-risk navigation
- configurable profile levels (strict/balanced/fast)
- monitor solve-time SLOs and per-challenge cost ceilings

**Warning signs:**
- Challenge solve time increases sharply after rollout
- Queue depth or worker saturation increases under same traffic
- Cost per successful solve trends upward

**Phase to address:**
Phase 4 - Performance tuning and policy controls.

---

### Pitfall 7: Over-claiming HumanCursor as full anti-bot solution

**What goes wrong:**
Migration is considered complete while fingerprinting/IP/challenge defenses still block flows.

**Why it happens:**
Mouse movement improvements are conflated with complete anti-detection coverage.

**How to avoid:**
Keep threat model explicit in roadmap:
- movement behavior is one signal only
- continue independent controls for browser fingerprinting, request patterns, and network reputation
- evaluate success on end-to-end solve outcomes, not cursor realism alone

**Warning signs:**
- Cursor telemetry improves but challenge pass rate does not
- Block pages remain correlated with network/session fingerprints
- Team discussions frame cursor migration as "final stealth fix"

**Phase to address:**
Phase 5 - End-to-end validation with layered detection signals.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Embed movement logic directly in `robotic` methods | Faster initial implementation | Hard-to-test orchestration; regression-prone diffs | Never (for this migration) |
| Hardcode jitter/overshoot constants globally | Quick tuning | No environment-specific control; unstable behavior across targets | Only temporary behind feature flag |
| Keep legacy and new engines without shared interface | Low refactor effort | Dual maintenance and inconsistent behavior contracts | Only during short A/B rollout window |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Playwright mouse API | Assuming `steps` interpolation is sufficient for realism | Generate explicit intermediate points + timing profile, then call `mouse.move` per point |
| hCaptcha interaction flow | Asserting final click location only | Assert full interaction sequence and challenge outcome metrics |
| Browser backend compatibility | Assuming same movement behavior across engines | Define supported browser matrix and run parity checks per backend |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| High-fidelity movement on all actions | Solve duration spikes and worker backlog grows | Selective realism policy by interaction type | Medium/high traffic with concurrent sessions |
| Per-step sleep without bounded profile | Large variance in completion times | Use bounded timing envelopes and SLO checks | CI and production under noisy runtime |
| Recomputing heavy path logic repeatedly | CPU overhead in hot loops | Cache/reuse path primitives where safe | Multi-session execution |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Treating cursor realism as anti-bot completeness | False confidence; unresolved detection vectors | Keep layered defenses and independent telemetry for each vector |
| Injecting debug cursor overlays in production runs | Leaks deterministic automation artifacts | Restrict debug visualization to local/test mode |
| Expanding JS injection surface for movement hooks without review | New script execution risk in challenge pages | Keep injection minimal and reviewed, with strict gating flags |

## "Looks Done But Isn't" Checklist

- [ ] **Parity:** Movement "looks human" in videos, but quantitative parity thresholds are not defined or enforced.
- [ ] **Reliability:** Happy-path tests pass, but retry/timeout/error-rate regression is not compared against baseline.
- [ ] **Compatibility:** Primary browser works, but supported browser matrix is not validated.
- [ ] **Performance:** Behavior improved, but throughput/cost SLOs were not re-verified.
- [ ] **Scope control:** Team assumes anti-bot problem solved without validating non-cursor detection signals.

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| No parity baselines | Phase 1 - Baseline & benchmarks | Baseline dashboard + regression gates merged |
| Native interpolation mistaken for realism | Phase 2 - Movement profile engine | Path/timing tests prove non-linear variable profile |
| Event semantics drift | Phase 3 - Contract tests | Event-order assertions pass on critical flows |
| Coordinate drift on dynamic UI | Phase 2 - Target revalidation integration | Miss-click and stale-target failures reduced |
| Fragile orchestration coupling | Phase 0 - Adapter extraction | Movement engine can be unit-tested without browser |
| Throughput collapse | Phase 4 - Performance policy tuning | Solve-time SLO and queue metrics within thresholds |
| Over-claiming anti-bot coverage | Phase 5 - End-to-end validation | Solve outcomes validated across cursor + non-cursor signals |

## Sources

- Playwright Mouse API (official docs, HIGH): https://playwright.dev/docs/api/class-mouse
- MDN `mousemove` event semantics (official docs, HIGH): https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event
- HumanCursor package documentation (official package docs, HIGH): https://pypi.org/project/HumanCursor/
- HumanCursor repository (official project source, MEDIUM): https://github.com/riflosnake/HumanCursor
- Community implementation patterns and failure discussions (Web research, LOW-MEDIUM; validate in phase execution):
  - https://bytetunnels.com/posts/browser-automation-human-like-mouse-movement/
  - https://substack.thewebscraping.club/p/bypass-datadome-mouse-movements-in-playwright
  - https://www.zenrows.com/blog/humancursor

---
*Pitfalls research for: cursor movement migration in hcaptcha-challenger*
*Researched: 2026-04-30*
