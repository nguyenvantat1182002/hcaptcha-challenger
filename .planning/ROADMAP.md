# Roadmap: Spatial Reasoning Engine V2

## Overview
This roadmap outlines the plan to enhance hCaptcha-challenger's object coordinate recognition by refining the visual grid system and the reasoning prompts for LLMs.

---

## Phase 1: High-Contrast Grid & Explicit Labeling
**Goal**: Reduce cell confusion by making the grid more "scientific" and clearly labeled.
- **Task 1.1**: Update `create_coordinate_grid.py` to include explicit X and Y axis labels on every major grid line.
- **Task 1.2**: Implement "Banded Grid" mode where alternating rows and columns have a subtle color tint for better visual separation.
- **Task 1.3**: Extend the grid customization config in `models.py` (CoordinateGrid) for these new features.

---

## Phase 2: Structural Prompt Engineering (CoT-Spatial)
**Goal**: Guide the LLM to think in terms of grid cells before calculating precise coordinates.
- **Task 2.1**: Refactor `point.md`, `bbox.md`, and `path.md` systems prompts.
- **Task 2.2**: Template a reasoning steps in the prompt: (1) Identify object, (2) Identify grid cell [Row, Col], (3) Map precise (x, y) within that cell.
- **Task 2.3**: Update `SpatialPointReasoner` and `SpatialPathReasoner` code if necessary to handle the new prompt structure.

---

## Phase 3: Zoom & Multi-Resolution Support (Optional/Experimental)
**Goal**: Address high-density challenges by zooming into suspected areas.
- **Task 3.1**: Implement a "Local Zoom" mechanism in `robotic_arm` or `challenger.py` that crops the suspected area and re-grids it for refined analysis.
- **Task 3.2**: Add logic to `AgentV` to trigger a "Refine" step if LLM confidence is low or a retry is triggered.

---

## Phase 4: Validation & Benchmarking
**Goal**: Quantify the accuracy improvement.
- **Task 4.1**: Create a benchmarking script using a set of static hCapcha challenges (e.g., area selection "Click on every boat").
- **Task 4.2**: Verify consistency between Gemini Pro (SCoT) and Gemini Flash.
- **Task 4.3**: UAT verification using the `RiotGames` login flow.

---

## STATE: Initializing
- [ ] Phase 1: Not started
- [ ] Phase 2: Not started
- [ ] Phase 3: Not started
- [ ] Phase 4: Not started

---
*Last updated: 2026-04-05 after initialization*
