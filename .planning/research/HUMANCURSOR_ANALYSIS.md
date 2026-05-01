# HumanCursor Library Analysis

**Project:** hcaptcha-challenger
**Researched:** 2025-05-22
**Overall confidence:** HIGH

## Executive Summary

`HumanCursor` is a Python library designed to simulate human-like mouse movements to bypass bot detection systems. It achieves this by generating non-linear trajectories using Bezier curves, applying Gaussian distortion for micro-jitters, and using easing functions (tweening) to vary velocity profiles. The library provides high-level APIs for both browser-based (`WebCursor` via Selenium) and system-wide (`SystemCursor` via PyAutoGUI) automation.

## Key Findings

### API Structure

The library is organized around two main interface classes:

1.  **`WebCursor(driver)`**:
    *   **Dependency**: `selenium`.
    *   **Purpose**: Controls the cursor within a web browser.
    *   **Key Methods**:
        *   `move_to([x, y])`: Moves to coordinates.
        *   `click_on(element_or_coords)`: Clicks a target.
        *   `drag_and_drop(source, destination)`: Performs drag operations.
        *   `control_scroll_bar(element, percentage)`: Handles scrolling.

2.  **`SystemCursor()`**:
    *   **Dependency**: `pyautogui`.
    *   **Purpose**: Controls the OS-level cursor.
    *   **Key Methods**: Same as `WebCursor`.

### Trajectory Generation Logic

The core logic resides in `humancursor/utilities/human_curve_generator.py` and `humancursor/utilities/calculate_and_randomize.py`.

*   **Algorithm**: N-degree Bezier Curve.
*   **Control Points**:
    *   Start point
    *   Randomly generated "internal knots" within a calculated boundary.
    *   End point
*   **Refinement**:
    *   **Distortion**: Gaussian noise (via `np.random.normal`) added to Y-coordinates of intermediate points to simulate hand instability.
    *   **Tweening**: Re-sampling of points using `pytweening` functions (e.g., `easeOutQuad`, `easeInOutQuint`) to create realistic acceleration/deceleration.
*   **Randomization**: `calculate_and_randomize.py` defines "natural" ranges for knots count (usually 2-5), distortion frequency, and boundary offsets based on distance.

### Dependencies

*   `numpy`: Used for efficient array operations and statistical distributions (normal, choice).
*   `pytweening`: Provides standard easing functions.
*   `selenium`: Required for `WebCursor`.
*   `pyautogui`: Required for `SystemCursor`.
*   `python-pynput` (Optional): Used in some utility/test contexts for listener support.

## Integration Points for hcaptcha-challenger

`hcaptcha-challenger` can integrate `HumanCursor` at several levels:

### 1. Payload Generation (High Priority)
The `HumanizeMouseTrajectory` class can be used standalone to generate the `motionData` required by hCaptcha. Instead of manual implementation, using the library ensures consistency with community-tested "human" patterns.
*   **Target**: `src/hcaptcha_challenger/agent/mouse.py`
*   **Action**: Replace inlined `_calculate_bezier_points`, `_distort_points`, etc., with calls to `HumanizeMouseTrajectory`.

### 2. Browser Interaction (Medium Priority)
If the project uses Selenium or Playwright, `WebCursor` (or a custom wrapper for Playwright) can handle the actual clicks on challenge tiles.
*   **Target**: `src/hcaptcha_challenger/agent/navigator.py` (or similar browser-driving code).
*   **Action**: Use `WebCursor` to perform the clicks on the `<img>` elements of the hCaptcha iframe.

### 3. DrissionPage Compatibility
Since `hcaptcha-challenger` uses `drissionpage`, a custom adapter for `HumanCursor` may be needed, as `HumanCursor` natively supports only Selenium and PyAutoGUI.
*   **Action**: Create a `DrissionCursor` that inherits from or wraps `SystemCursor` but uses `drissionpage`'s coordinate system and click methods.

## Pitfalls & Considerations

*   **Coordinates**: `WebCursor` uses browser-relative coordinates. hCaptcha often uses iframe-relative coordinates or global coordinates depending on the detection layer. Correct offset calculation is critical.
*   **Speed vs. Reliability**: Overly complex curves may take too long, causing the hCaptcha challenge to time out. `HumanCursor`'s `target_points` and `tweening` should be tuned for the specific timing requirements of hCaptcha (usually 100ms - 500ms for a movement).
*   **Determinism**: Ensure that randomization is truly random and doesn't produce identical paths for different challenges, which is a common footprint for bot detection.

## Sources

*   [HumanCursor GitHub Repository](https://github.com/riflosnake/HumanCursor)
*   [HumanizeMouseTrajectory Source](https://github.com/riflosnake/HumanCursor/blob/main/humancursor/utilities/human_curve_generator.py)
*   [PyProject.toml Dependencies](https://github.com/riflosnake/HumanCursor/blob/main/pyproject.toml)
