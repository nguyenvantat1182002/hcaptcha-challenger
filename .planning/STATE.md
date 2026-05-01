# Project State: HumanCursor Integration

## Overview
We are replacing the custom human-like cursor algorithm with the `humancursor` library.

## Current Milestones
- **Research:** Completed. Found that `humancursor` is designed for Selenium but can be adapted.
- **Requirements:** Defined.
- **Roadmap:** Defined.
- **Phase 1 Context:** Gathered. Decisions on integration strategy and prototype goal are locked.

## Active Tasks
- Phase 1: Planning implementation and prototype development.

## Blockers
- None.

## Memory Points
- Current `mouse.py` is very complex and contains inlined `pytweening` logic.
- `DrissionPageMouse` in `robotic.py` already uses a custom `move` method to bypass linear interpolation. This is the key injection point.
