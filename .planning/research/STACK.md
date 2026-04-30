# Stack Research

**Domain:** HumanCursor-style movement migration for Python web automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10+ | Runtime for solver and movement engine | Matches existing codebase and typing/tooling baseline. |
| Playwright | 1.40+ | Browser/session automation control | Stable event timing and page interaction primitives for movement replay. |
| NumPy | 1.26+ | Curve and velocity profile math | Reliable vector math for bezier/spline trajectories and sampling. |
| SciPy (optional) | 1.11+ | Interpolation/smoothing helpers | Useful if advanced jerk-limited paths are required. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HumanCursor-style reference model | latest | Behavioral reference for path/velocity shape | Use for parity benchmarks and fixture generation, not direct runtime coupling. |
| pydantic | 2.x | Typed movement profile configs | Use for stable profile schemas and migration-safe defaults. |
| pytest + pytest-benchmark | 8.x | Correctness and perf regression checks | Use for deterministic path quality and runtime budget validation. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Ruff | Lint/import hygiene | Keep movement module consistent with existing style. |
| Black | Formatting | Prevent noise in trajectory math refactors. |
| Ty (type checker) | Type safety | Catch profile/strategy contract drift early. |

## Installation

```bash
# Core
uv add numpy

# Optional interpolation helpers
uv add scipy

# Dev / validation
uv add --dev pytest-benchmark
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Playwright/DrissionPage event path | OS-level cursor APIs | Use only if future scope expands to native/system cursor automation. |
| NumPy-based trajectory engine | Pure-Python loops only | Acceptable for prototypes; less maintainable for complex profiles. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Hardcoded linear interpolation | Unrealistic motion signature, poor parity | Curved path + variable velocity profile. |
| Randomness-only "humanization" | Non-reproducible regressions | Seeded stochastic model with benchmark envelopes. |
| Direct dependency on third-party runtime internals | Fragile upgrades and hidden breakage | Adapter layer with explicit profile contracts. |

## Stack Patterns by Variant

**If strict compatibility mode:**
- Keep existing public API and wrap new engine behind strategy interface.
- Because migration risk is minimized and rollback is straightforward.

**If parity-first rollout mode:**
- Add optional new profile/config API while retaining compatibility defaults.
- Because it enables fine-grained tuning without breaking existing flows.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| playwright>=1.40 | python>=3.10 | Aligns with project baseline and CI tooling. |
| numpy>=1.26 | python>=3.10 | Avoids deprecated APIs from older Python versions. |

## Sources

- Existing codebase stack docs: `.planning/codebase/STACK.md`
- Existing architecture docs: `.planning/codebase/ARCHITECTURE.md`
- HumanCursor reference repository: [riflosnake/HumanCursor](https://github.com/riflosnake/HumanCursor)

---
*Stack research for: HumanCursor-style movement migration*
*Researched: 2026-04-30*
