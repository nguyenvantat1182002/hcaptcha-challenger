# Project: Spatial Reasoning Engine V2

## What This Is
An enhancement to `hcaptcha-challenger` specifically targeting spatial reasoning accuracy. The current LLM-based solvers sometimes confuse grid cells or struggle with precise coordinate mapping. This project aims to improve the grid visualization system and the underlying geometric reasoning prompts.

## Core Value
High-precision coordinate extraction for complex challenges (e.g., area selection, drag-and-drop) while minimizing retry rates and cost.

## Context
- **Base Stack**: Playwright, Python, LLM (Gemini 2.5/3.1).
- **Current State**: Uses a Matplotlib-generated grid overlay (`create_coordinate_grid.py`) and various spatial analyst models (`point.py`, `bbox.py`).
- **The Problem**: LLM "hallucinates" or shifts coordinates by misidentifying the correct grid cell in the overlay.

## Requirements

### Active
- [ ] Implement clear numerical cell labels (X/Y axis) in `create_coordinate_grid.py`.
- [ ] Add alternating row/column color banding to increase cell contrast.
- [ ] Update `point.md`, `bbox.md`, and `path.md` prompts to enforce a systematic cell-by-cell reasoning workflow.
- [ ] Add a "Geometric Verification" stage where the LLM must confirm the cell ID before calculating the precise (x, y) point.
- [ ] Standardize the communication format for coordinate outputs across all reasoners.

### Out of Scope
- Building a custom visual model from scratch.
- Real-time video processing.

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Gemini 3 Flash | Best balance of speed, vision context length, and cost | — Pending |

## Evolution
This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-04-05 after initialization*
