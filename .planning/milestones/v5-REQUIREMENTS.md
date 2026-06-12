# Milestone 5: Relative Coordinate System

## 1. Grid Normalization
- [ ] Update `create_coordinate_grid` (and `_create_adaptive_contrast_grid`) in `src/hcaptcha_challenger/helper/create_coordinate_grid.py` to plot the coordinate axes starting from `(0, 0)` up to `(width, height)`.
- [ ] Ensure that the visual ticks rendered on the output image display relative values `[0, X]` and `[0, Y]` instead of absolute page coordinates (e.g. `100, 200`).

## 2. Coordinate Translation
- [ ] Since the Visual LLMs will now output relative coordinates based on the normalized grid, update the click action handlers in `src/hcaptcha_challenger/agent/robotic_arm.py` (specifically `challenge_image_drag_drop` and `challenge_image_label_select`).
- [ ] The coordinates returned by the Reasoner must be translated back to absolute page coordinates by adding the original bounding box `x` and `y` offsets before executing `self.page.mouse.click` and `self._perform_drag_drop`.
- [ ] Update `_capture_spatial_mapping` to return the `bbox` so that the calling methods have the required `x` and `y` offsets for translation.
