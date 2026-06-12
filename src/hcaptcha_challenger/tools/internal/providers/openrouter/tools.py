from pydantic import BaseModel, Field
from openai import pydantic_function_tool


class ClickCoordinates(BaseModel):
    """Simulate selecting coordinates on a captcha image."""

    x: int = Field(..., description="The x-coordinate of the target to click.")
    y: int = Field(..., description="The y-coordinate of the target to click.")


# Wrap the tool in OpenAI's expected format
click_coordinates_tool = pydantic_function_tool(ClickCoordinates)
