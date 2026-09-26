import asyncio
import math
import random

from playwright.async_api import Locator, Page

from hcaptcha_challenger.models import SpatialPath


def generate_bezier_trajectory(
    start: tuple[float, float], end: tuple[float, float], steps: int
) -> list[tuple[float, float]]:
    """
    Generates a quadratic bezier curve trajectory between start and end points.
    """
    points = []
    distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

    # For longer distances, we use a higher control point offset
    offset_factor = min(0.3, max(0.1, distance / 1000))

    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2

    # Create slight randomness in the control point
    control_x = mid_x + random.uniform(-1, 1) * distance * offset_factor
    control_y = mid_y + random.uniform(-1, 1) * distance * offset_factor

    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control_x + t**2 * end[0]
        y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control_y + t**2 * end[1]
        points.append((x, y))

    return points


def generate_dynamic_delays(steps: int, base_delay: int) -> list[float]:
    """
    Generates dynamic delays between mouse movements to simulate human-like acceleration/deceleration.
    """
    delays = []

    for i in range(steps + 1):
        progress = i / steps

        # Ease in-out function (slow start, fast middle, slow end)
        if progress < 0.5:
            factor = 2 * progress * progress
        else:
            progress = progress - 1
            factor = 1 - (-2 * progress * progress)

        # Adjust delay based on position in the curve (1.5x at ends, 0.6x in middle)
        delay_factor = 1.5 - 0.9 * factor
        random_factor = random.uniform(0.9, 1.1)

        delays.append(base_delay * delay_factor * random_factor)

    return delays


# Aliases for backward compatibility
_generate_bezier_trajectory = generate_bezier_trajectory
_generate_dynamic_delays = generate_dynamic_delays


class HumanoidPointer:
    """
    Simulates human-like pointer kinematics (smooth Bezier motion, ease-in-out velocity, and micro-jitter).
    """

    def __init__(self, page: Page, disable_bezier_trajectory: bool = False):
        self.page = page
        self.disable_bezier_trajectory = disable_bezier_trajectory

    async def click(self, locator: Locator, delay: int = 150) -> None:
        """
        Moves the mouse to the center of the given locator and clicks.
        """
        bbox = await locator.bounding_box()
        if bbox is None:
            raise ValueError("Element is not visible or does not exist")

        center_x = bbox["x"] + bbox["width"] / 2
        center_y = bbox["y"] + bbox["height"] / 2

        await self.page.mouse.move(center_x, center_y)
        await self.page.mouse.click(center_x, center_y, delay=delay)

    async def click_at(self, x: float, y: float, delay: int = 180) -> None:
        """
        Clicks at specific screen coordinates.
        """
        await self.page.mouse.click(x, y, delay=delay)

    async def drag(self, path: SpatialPath, steps: int = 25, delay_ms: int = 15) -> None:
        """
        Performs a human-like drag and drop operation using bezier curve trajectory.
        """
        start_x, start_y = path.start_point.x, path.start_point.y
        end_x, end_y = path.end_point.x, path.end_point.y

        if self.disable_bezier_trajectory:
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            await self.page.mouse.move(end_x, end_y)
            await self.page.mouse.up()
            return

        # Move to the starting position
        await self.page.mouse.move(start_x, start_y)

        # Small random delay before pressing down (human reaction time)
        await asyncio.sleep(random.uniform(0.05, 0.15))

        # Press the mouse button down
        await self.page.mouse.down()

        # Generate a bezier curve path with a control point
        points = generate_bezier_trajectory((start_x, start_y), (end_x, end_y), steps)
        delays = generate_dynamic_delays(steps, base_delay=delay_ms)

        # Perform the drag with human-like movement
        for i, ((current_x, current_y), delay) in enumerate(zip(points, delays)):
            # Add slight "noise" to the path (more pronounced near the end)
            if i > steps * 0.7:
                noise_factor = 0.5 if i > steps * 0.9 else 0.2
                current_x += random.uniform(-noise_factor, noise_factor)
                current_y += random.uniform(-noise_factor, noise_factor)

            await self.page.mouse.move(current_x, current_y)
            await asyncio.sleep(delay / 1000)

        # Ensure we end exactly at the target position
        await self.page.mouse.move(end_x, end_y)

        # Small pause before releasing (human precision adjustment)
        await asyncio.sleep(random.uniform(0.05, 0.1))

        # Release the mouse button at the destination
        await self.page.mouse.up()

        # Small pause between drag operations
        await asyncio.sleep(random.uniform(0.08, 0.12))
