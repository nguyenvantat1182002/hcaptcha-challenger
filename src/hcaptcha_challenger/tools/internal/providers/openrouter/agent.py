from typing import Any, Dict, List

from openai import AsyncOpenAI
from pyee.asyncio import AsyncIOEventEmitter


class Agent(AsyncIOEventEmitter):
    """
    Asynchronous OpenRouter Agent that streams responses and emits events.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openrouter/auto",
        instructions: str = "You are a helpful assistant.",
        max_steps: int = 5,
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        super().__init__()
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.config = {
            "model": model,
            "instructions": instructions,
            "max_steps": max_steps,
        }
        self.messages: List[Dict[str, Any]] = []
        self.tools: List[Any] = []

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return list(self.messages)

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()

    def set_instructions(self, instructions: str) -> None:
        """Update the system instructions."""
        self.config["instructions"] = instructions

    def add_tool(self, tool: Any) -> None:
        """
        Add a tool for the agent to use.
        Supports pydantic_function_tool formats from openai SDK.
        """
        self.tools.append(tool)

    async def send(self, content: str) -> str:
        """
        Send a message to the agent and stream the response.
        """
        user_message = {"role": "user", "content": content}
        self.messages.append(user_message)
        self.emit("message:user", user_message)
        self.emit("thinking:start")

        api_messages = [
            {"role": "system", "content": self.config["instructions"]}
        ] + self.messages

        try:
            kwargs = {
                "model": self.config["model"],
                "messages": api_messages,
                "stream": True,
            }
            if self.tools:
                kwargs["tools"] = self.tools

            response_stream = await self.client.chat.completions.create(**kwargs)

            self.emit("stream:start")
            full_text = ""
            assistant_message = {"role": "assistant", "content": ""}

            async for chunk in response_stream:
                self.emit("item:update", chunk)

                if chunk.choices:
                    delta = chunk.choices[0].delta

                    if delta.content is not None:
                        new_text = delta.content
                        full_text += new_text
                        self.emit("stream:delta", new_text, full_text)

                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            self.emit("tool:call", tool_call)

            assistant_message["content"] = full_text
            self.messages.append(assistant_message)
            self.emit("message:assistant", assistant_message)
            self.emit("stream:end", full_text)

            return full_text

        except Exception as e:
            self.emit("error", e)
            raise e
        finally:
            self.emit("thinking:end")
