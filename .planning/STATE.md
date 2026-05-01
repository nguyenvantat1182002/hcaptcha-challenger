# Project State: HumanCursor Integration

## Overview
We are replacing the custom human-like cursor algorithm with the `humancursor` library.

## Current Milestones
- **Research:** Completed. Found that `humancursor` is designed for Selenium but can be adapted.
- **Requirements:** Defined.
- **Roadmap:** Defined.

## Active Tasks
- Phase 1: Prototype `humancursor` + `DrissionPage` integration.

## Blockers
- None.

## Memory Points
- Current `mouse.py` is very complex and contains inlined `pytweening` logic.
- `DrissionPageMouse` in `robotic.py` already uses a custom `move` method to bypass linear interpolation. This is the key injection point.
