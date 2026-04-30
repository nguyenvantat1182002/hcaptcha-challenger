# Stack Research

**Domain:** HumanCursor-style web cursor motion for Python hCaptcha browser automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Playwright Python | `>=1.45,<2` | Browser mouse event execution (`mouse.move/down/up/wheel`) | It is the most stable low-level web mouse API with explicit interpolated move steps, trace tooling, and long-term maintenance. Use this as the event emitter; do not delegate core movement semantics to an unmaintained wrapper. | HIGH |
| NumPy | `>=2.0,<3` | Fast vector math + reproducible random sampling | Cursor paths need cheap vector operations and controllable randomness. NumPy `Generator` enables seeded reproducibility for deterministic test runs while allowing realistic stochastic variation in production profiles. | HIGH |
| SciPy (interpolate + stats) | `>=1.13,<2` | Parametric spline generation and parity testing utilities | `scipy.interpolate` gives robust spline/B-spline primitives to implement HumanCursor-like curves without re-inventing numerics. `scipy.stats` is useful for movement-profile parity checks (distribution similarity, outlier detection). | HIGH |
| Pydantic Settings (existing project standard) | `>=2.7,<3` | Typed motion profile config and environment toggles | Keep migration maintainable by encoding movement knobs (speed, jitter, seed mode, easing profile) as validated config models aligned with current project conventions. | HIGH |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `pytweening` | `>=1.2,<2` | Easing curves (ease-in/out families) for velocity envelopes | Use when you want HumanCursor-like acceleration/deceleration profiles with minimal custom math and easy profile swapping. | MEDIUM |
| `typing-extensions` | `>=4.12` (if needed by py310 typing) | Strong typing for protocolized movement engine interfaces | Use for precise protocol/type contracts if Python 3.10 typing limitations appear in movement abstraction layer. | MEDIUM |
| `pytest` + `pytest-asyncio` (already in project) | project-managed | Regression and parity validation harness | Use to lock deterministic seeded trajectories and verify no behavioral regressions in click/drag workflows. | HIGH |

### Development Tools

| Tool | Purpose | Notes | Confidence |
|------|---------|-------|------------|
| Playwright Trace Viewer | Visual motion verification (red-dot path inspection) | Capture trace in CI/debug sessions for path audits; this is the fastest way to validate emitted mouse events match expected trajectories. | HIGH |
| Ruff + Black (existing) | Keep algorithm code readable and uniform | Enforce strict style for numerics-heavy code to reduce maintenance burden and accidental logic drift. | HIGH |

## Installation

```bash
# Core motion stack
uv add "playwright>=1.45,<2" "numpy>=2.0,<3" "scipy>=1.13,<2" "pydantic>=2.7,<3" "pydantic-settings>=2.3,<3"

# Optional easing helper
uv add "pytweening>=1.2,<2"

# If browser binaries are missing
playwright install chromium
```

## Prescriptive Implementation Approach (2026 Standard)

1. Build an internal `CursorMotionEngine` abstraction with two modes:
   - **Realistic mode (default):** seeded-per-session stochastic curve generation with bounded jitter.
   - **Deterministic mode (tests/debug):** fixed seed and fixed profile for byte-stable replay.
2. Generate trajectories with NumPy + SciPy (`splprep/splev` or `make_interp_spline`) from start/end + randomized control points constrained by distance bands.
3. Convert sampled path points to Playwright `mouse.move(..., steps=...)` segments, then emit click/drag primitives with realistic pause envelopes.
4. Store all movement profile parameters in typed config (Pydantic), not ad-hoc constants.
5. Add parity metrics tests (path curvature, velocity distribution, dwell times) to prevent regressions during future tuning.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Internal Playwright-native engine | `humancursor-playwright` package | Only for rapid prototyping. Current package metadata references placeholder repos and beta maturity; not ideal as a long-term production dependency. |
| NumPy + SciPy interpolation | Pure hand-rolled Bezier math only | Acceptable if you want zero SciPy dependency and can maintain your own robust interpolation + test suite. |
| Pydantic-validated motion profiles | Hardcoded constants in movement class | Never preferred for this codebase; only acceptable for temporary spike experiments. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `humancursor` (PyPI `HumanCursor` v1.1.5) as direct dependency | Last release is from 2023, Selenium-centric, and explicitly framed around bot-evasion language; mismatch for current Playwright/maintainability goals. | Internal Playwright-native engine using NumPy/SciPy primitives. |
| `pyautogui`-based cursor control for web path | System-level cursor automation is brittle in headless/CI and not aligned with browser event model used by Playwright. | Browser-native `page.mouse` event emission. |
| Copy-pasted community snippets from StackOverflow as core algorithm | High drift risk, unclear licensing/maintenance, and weak testability for long-term project evolution. | Encapsulated internal motion module with tested math primitives. |

## Stack Patterns by Variant

**If priority is realism in production runs:**
- Use stochastic profile buckets by distance (short/medium/long), randomized control points, and easing noise.
- Because human-like behavior emerges from constrained randomness, not static deterministic curves.

**If priority is deterministic reproducibility (CI/regression):**
- Use fixed RNG seed, fixed curve family, disabled random micro-jitter, and fixed dwell windows.
- Because stable replay is required to detect algorithm regressions with low false positives.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `playwright>=1.45,<2` | Python `>=3.10` | Aligns with current project baseline and modern async APIs. |
| `numpy>=2.0,<3` | `scipy>=1.13,<2` | Choose tested pair ranges in lockfile; validate on CI matrix once pinned. |
| `pydantic>=2.7,<3` | `pydantic-settings>=2.3,<3` | Matches existing project configuration pattern. |

## Sources

- https://playwright.dev/python/docs/api/class-mouse — Playwright mouse primitives and interpolation semantics (`steps`) (HIGH)
- https://playwright.dev/python/docs/input — Drag/drop and low-level mouse behavior guidance (HIGH)
- https://docs.scipy.org/doc/scipy/reference/interpolate.html — Current interpolation APIs and deprecation status (HIGH)
- https://pypi.org/project/HumanCursor/ — HumanCursor package scope, dependencies, and release recency (MEDIUM)
- https://pypi.org/project/humancursor-playwright/ — Playwright adaptation status and maturity signals (MEDIUM)

---
*Stack research for: HumanCursor-style cursor migration in hcaptcha-challenger*
*Researched: 2026-04-30*
