# Project: Replace Cursor Movement Algorithm with HumanCursor

**Status:** Initialized
**Owner:** Gemini CLI
**Date:** 2026-05-01

## Context
The current human-like cursor movement algorithm in `hcaptcha-challenger` is a custom implementation inspired by `HumanCursor`. To improve reliability, realism, and maintainability, we are replacing it entirely with the official `humancursor` library (v1.1.5).

## Goals
- Complete removal of the existing custom Bezier/trajectory logic in `mouse.py`.
- Full integration of the `humancursor` library.
- Maintain existing DrissionPage and browser automation capabilities.
- Ensure "human-like" behavior through visual and standard integration tests.

## Key Decisions
- **Full Replacement:** The old algorithm will be removed entirely, not kept as a fallback.
- **DrissionPage Compatibility:** Since `humancursor` primarily targets Selenium, we will implement an adapter or coordination layer to use it with DrissionPage (which the project uses).
- **Configuration:** We will align `AgentConfig` with `humancursor`'s parameters where possible.
