# Pitfalls Research

**Domain:** HumanCursor-style cursor migration for browser captcha automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Breaking Existing Movement API Contracts

**What goes wrong:**
Existing solver call sites fail or silently change behavior after migration.

**Why it happens:**
Teams optimize for new engine design and underweight backward compatibility.

**How to avoid:**
Introduce compatibility adapter first; enforce contract tests before swapping internals.

**Warning signs:**
Large diffs in `robotic.py` call signatures and fixture updates touching many unrelated tests.

**Phase to address:**
Phase 1 (engine scaffold + compatibility bridge).

---

### Pitfall 2: Non-Deterministic Regression Testing

**What goes wrong:**
CI failures are flaky and movement quality regressions cannot be reproduced.

**Why it happens:**
Random perturbations are introduced without seed control or benchmark baselines.

**How to avoid:**
Add deterministic mode with explicit seeds and parity metric snapshots.

**Warning signs:**
Intermittent parity-score drift across identical commits.

**Phase to address:**
Phase 2 (benchmarking and validation).

---

### Pitfall 3: Overfitting to a Single Demo Pattern

**What goes wrong:**
Algorithm appears good in one scenario but fails across target distances, element sizes, and drag paths.

**Why it happens:**
Validation dataset is too narrow and lacks edge-case coverage.

**How to avoid:**
Build benchmark matrix (short/long moves, diagonal, drag, constrained targets).

**Warning signs:**
Good average score with poor percentile tails in specific motion classes.

**Phase to address:**
Phase 2 and Phase 3 (integration hardening).

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Inline curve math in orchestrator | Faster initial patch | Hard debugging and code coupling | Never for this migration. |
| Skip profile schema typing | Less boilerplate | Hidden behavior drift and config bugs | Only for throwaway spikes. |
| No benchmark threshold gates | Faster merge cycle | Silent quality degradation | Never once migration starts. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| DrissionPage/Playwright actions | Sending too many micro-steps with inconsistent timing | Use bounded step count + calibrated delays. |
| Existing retry logic | Reusing old retries without motion-state awareness | Reset/adapt movement profile on retry attempts. |
| CLI config | Hardcoding behavior with no explicit flags | Expose profile + deterministic toggles in config. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Excessive path points | Slow interaction and timeouts | Dynamic sampling by distance and complexity | Frequent long-distance moves. |
| Heavy per-move allocations | CPU spikes in batch runs | Preallocate arrays and reuse profile objects | Medium/high concurrency. |
| Benchmark on every runtime action | Throughput collapse | Gate full metrics to test/diagnostic mode | Production solver loops. |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Enabling aggressive anti-bot heuristics by default | Policy/legal exposure | Keep scope to realistic motion for stability/testing. |
| Logging raw challenge metadata excessively | Sensitive telemetry leakage | Minimize logs and redact identifiers. |
| External fetches during movement runtime | Supply-chain/runtime variability | Vendor/pin dependencies and keep runtime deterministic. |

## "Looks Done But Isn't" Checklist

- [ ] **Compatibility:** Old API call signatures still pass contract tests.
- [ ] **Parity:** Quantitative metrics pass threshold, not just visual checks.
- [ ] **Stability:** Deterministic mode reproducibly matches baseline.
- [ ] **Integration:** Full challenge solve path validated, not isolated movement unit only.

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| API contract breakage | Phase 1 | Compatibility test suite all green. |
| Flaky/non-deterministic validation | Phase 2 | Seeded benchmark run stable across CI reruns. |
| Overfit trajectory model | Phase 3 | Benchmark matrix percentiles meet thresholds. |

## Sources

- `.planning/codebase/CONCERNS.md`
- `.planning/codebase/ARCHITECTURE.md`
- HumanCursor reference: [riflosnake/HumanCursor](https://github.com/riflosnake/HumanCursor)

---
*Pitfalls research for: cursor movement migration*
*Researched: 2026-04-30*
