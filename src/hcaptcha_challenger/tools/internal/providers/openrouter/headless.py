import asyncio
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any

from hcaptcha_challenger.tools.internal.providers.openrouter.agent import Agent
from hcaptcha_challenger.tools.internal.providers.openrouter.tools import (
    click_coordinates_tool,
)


class Settings(BaseSettings):
    openrouter_api_key: str = "sk-or-v1-dummy"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


async def main() -> None:
    settings = Settings()
    api_key = settings.openrouter_api_key

    agent = Agent(api_key=api_key)

    # Attach tool
    agent.add_tool(click_coordinates_tool)

    # Register listeners
    @agent.on("stream:delta")
    def on_stream_delta(new_text: str, full_text: str) -> None:
        print(new_text, end="", flush=True)

    @agent.on("tool:call")
    def on_tool_call(tool_call: Any) -> None:
        print("\n\n[TOOL CALL TRIGGERED]")
        print(f"ID: {tool_call.id}")
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")

    print("Sending prompt to Agent...\n")
    print("-" * 50)

    prompt = "Please solve the captcha by clicking on the cat. The cat is located at x=120, y=340."
    try:
        await agent.send(prompt)
    except Exception as e:
        print(
            f"\n[ERROR] Request failed (Did you set a valid OPENROUTER_API_KEY?): {e}"
        )

    print("\n" + "-" * 50)
    print("Execution Finished.")


if __name__ == "__main__":
    from typing import Any

    asyncio.run(main())
