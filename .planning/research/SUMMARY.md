# Project Research Summary

**Project:** hcaptcha-challenger
**Domain:** Brownfield migration of cursor movement engine in Python browser automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Executive Summary

This project is an algorithm migration inside an existing captcha-solving automation stack, not a greenfield build. The most effective approach is compatibility-first: keep current public behavior stable, insert a HumanCursor-style engine behind an adapter, and validate quality with deterministic parity benchmarks.

Research indicates the key risk is not just path realism but migration safety: API drift, flaky non-deterministic tests, and overfitting to narrow motion scenarios can derail rollout. A measured phase sequence should therefore establish compatibility contracts and deterministic validation before broad integration.

The recommended roadmap is a three-stage track: engine scaffold + adapter, parity and regression validation, then orchestrator-wide integration hardening. This structure directly supports the selected constraints and "done" definition.

## Key Findings

### Recommended Stack

Use the existing Python + Playwright/DrissionPage runtime and add a focused trajectory subsystem powered by typed profiles and vectorized math utilities. NumPy is sufficient for most trajectory generation needs; SciPy remains optional for advanced interpolation.

**Core technologies:**
- Python 3.10+ — existing runtime baseline and tooling compatibility.
- Playwright/DrissionPage — browser action execution path already in production.
- NumPy — stable path/velocity computation primitives for deterministic metrics.

### Expected Features

**Must have (table stakes):**
- HumanCursor-style curved path and variable velocity behavior.
- Backward-compatible API path and deterministic benchmark mode.

**Should have (competitive):**
- Parity scoring against reference behavior.
- Profile presets for different interaction styles.

**Defer (v2+):**
- Native/system cursor parity and broader anti-bot strategy expansion.

### Architecture Approach

Integrate a dedicated movement module under the agent layer and expose it through a compatibility adapter consumed by `robotic` orchestration. Keep benchmark and parity logic first-class in test/diagnostic boundaries, not embedded in runtime hot paths.

**Major components:**
1. Compatibility adapter — keeps current integration contract stable.
2. HumanCursor-style trajectory engine — generates points/timing based on profiles.
3. Benchmark/metrics harness — enforces migration quality gates.

### Critical Pitfalls

1. **API contract breakage** — prevent via adapter-first implementation and contract tests.
2. **Flaky validation from uncontrolled randomness** — prevent via deterministic seed mode.
3. **Overfitting to narrow demos** — prevent via benchmark matrix across move classes.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Engine Scaffold + Compatibility Layer
**Rationale:** Reduces migration risk before deep algorithm tuning.  
**Delivers:** Movement module, profile schema, adapter contracts.  
**Addresses:** Core replacement + compatibility table stakes.  
**Avoids:** Early API breakage pitfall.

### Phase 2: Parity Metrics + Regression Validation
**Rationale:** Locks objective "done" criteria before broad rollout.  
**Delivers:** Deterministic benchmark suite and acceptance thresholds.  
**Uses:** NumPy metrics, pytest benchmark tooling.  
**Implements:** Benchmark harness component.

### Phase 3: Full Web-Flow Integration Hardening
**Rationale:** Apply engine safely to all web movement paths after confidence exists.  
**Delivers:** Integrated move/click/drag behavior with stable solver outcomes.

### Phase Ordering Rationale

- Compatibility boundaries first, then quality gates, then broad integration.
- This order aligns with existing architecture dependencies and user-selected risk posture.
- It directly mitigates the top pitfalls discovered in research.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Exact parity metric definitions and threshold calibration.

Phases with standard patterns (skip deep research):
- **Phase 1:** Adapter + strategy extraction pattern is well-established.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Strong internal evidence; partial external verification. |
| Features | MEDIUM | Clear migration intent, but benchmark specifics need tuning. |
| Architecture | HIGH | Existing codebase mapping provides strong grounding. |
| Pitfalls | MEDIUM | Common migration risks are known; some thresholds remain project-specific. |

**Overall confidence:** MEDIUM

### Gaps to Address

- Finalize quantitative parity metric formula and thresholds during phase planning.
- Validate whether optional API extension is necessary after compatibility path is implemented.

## Sources

### Primary (HIGH confidence)
- `.planning/codebase/ARCHITECTURE.md` — current system structure and boundaries.
- `.planning/codebase/CONCERNS.md` — known integration risks and fragility points.

### Secondary (MEDIUM confidence)
- HumanCursor repository: [riflosnake/HumanCursor](https://github.com/riflosnake/HumanCursor) — reference behavior expectations.

---
*Research completed: 2026-04-30*
*Ready for roadmap: yes*
