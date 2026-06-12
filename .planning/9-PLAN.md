# Phase 9: Grid Normalization and Translation

## Objective
Normalize coordinate grid images to start from 0 for LLM inferences, and translate the LLM's relative coordinates back to absolute webpage coordinates before executing clicks/drags.

## Step 1: Update Grid Rendering Logic
**File**: `src/hcaptcha_challenger/helper/create_coordinate_grid.py`
- In `_create_adaptive_contrast_grid`:
  - Change `ax.set_xticklabels([str(round(tick)) for tick in x_ticks], ...)` to `ax.set_xticklabels([str(round(tick - x)) for tick in x_ticks], ...)`
  - Change `ax.set_yticklabels([str(round(tick)) for tick in y_ticks], ...)` to `ax.set_yticklabels([str(round(tick - y)) for tick in y_ticks], ...)`
- In `create_coordinate_grid`:
  - Change `ax.set_xticklabels([str(round(tick)) for tick in x_ticks])` to `ax.set_xticklabels([str(round(tick - x)) for tick in x_ticks])`
  - Change `ax.set_yticklabels([str(round(tick)) for tick in y_ticks])` to `ax.set_yticklabels([str(round(tick - y)) for tick in y_ticks])`

## Step 2: Extract BBox in Spatial Mapping
**File**: `src/hcaptcha_challenger/agent/robotic_arm.py`
- Modify `_capture_spatial_mapping` to return `(challenge_screenshot, grid_divisions, bbox)`.

## Step 3: Translate Coordinates in Select Challenge
**File**: `src/hcaptcha_challenger/agent/robotic_arm.py`
- In `challenge_image_label_select`, unpack `bbox` from `_capture_spatial_mapping`.
- When iterating through `response.points`, add `bbox['x']` and `bbox['y']` to `point.x` and `point.y` respectively in `self.page.mouse.click`.

## Step 4: Translate Coordinates in Drag Challenge
**File**: `src/hcaptcha_challenger/agent/robotic_arm.py`
- In `challenge_image_drag_drop`, unpack `bbox` from `_capture_spatial_mapping`.
- Iterate over `response.paths` and add `bbox['x']` to `path.start_point.x` and `path.end_point.x`. Add `bbox['y']` to `path.start_point.y` and `path.end_point.y` before calling `_perform_drag_drop`.

## Step 5: Verification
- Ensure `ruff` linting passes.
- Execute `demo_camoufox.py` and verify that clicks are performed accurately.
