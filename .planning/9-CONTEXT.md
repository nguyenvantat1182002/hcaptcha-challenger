# Phase 9: Context & Implementation Decisions

## Context
In previous phases, the spatial grid drawn over images was labeled with the absolute webpage coordinates (e.g., starting at `X=100`, `Y=200`). This meant that visual LLMs had to output those absolute coordinate numbers.
To improve accuracy, we want the grid to always start at `[0, 0]` relative to the top-left corner of the challenge image.

## Gray Areas & Decisions

### 1. Grid Rendering Strategy
- **Decision:** Modify `create_coordinate_grid` and `_create_adaptive_contrast_grid` in `src/hcaptcha_challenger/helper/create_coordinate_grid.py`.
- **Implementation Detail:** We will not change the `plt` extent/limits (to avoid messing up internal drawing logic). Instead, we will subtract `x` and `y` from `x_ticks` and `y_ticks` when generating the `xticklabels` and `yticklabels`.
  - From: `ax.set_xticklabels([str(round(tick)) for tick in x_ticks])`
  - To: `ax.set_xticklabels([str(round(tick - x)) for tick in x_ticks])`

### 2. Translating Coordinates
- **Decision:** Since the Visual LLMs will now return coordinates relative to the image (0-based), the `RoboticArm` must translate these back to absolute webpage coordinates before executing playwright clicks and drags.
- **Implementation Detail:** 
  - Update `_capture_spatial_mapping` to return a tuple of `(challenge_screenshot, grid_divisions, bbox)`.
  - In `challenge_image_drag_drop`: offset `path.start_point` and `path.end_point` by `bbox['x']` and `bbox['y']`.
  - In `challenge_image_label_select`: offset `point.x` and `point.y` by `bbox['x']` and `bbox['y']`.

### 3. Edge Cases & Scope
- **Image Classifier (9-grid):** This tool uses indices `[0,0] ~ [2,2]`, so it does not rely on pixel coordinate grids and is unaffected by this change.
- **Backward Compatibility:** Because coordinate shifting happens transparently between the grid generation and `RoboticArm`, other layers of the application are completely unaffected.

## Next Steps
Proceed to `/gsd-plan-phase 9`.
