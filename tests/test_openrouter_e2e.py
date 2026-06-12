import pytest
from pathlib import Path

from hcaptcha_challenger.agent.challenger import AgentConfig
from hcaptcha_challenger.tools.image_classifier import ImageClassifier
from hcaptcha_challenger.models import ImageBinaryChallenge


@pytest.mark.asyncio
async def test_image_classifier_openrouter():
    """
    Test E2E integration with OpenRouter for the ImageClassifier tool.
    Dynamically loads configuration and calls the provider to parse a structured response.
    """
    try:
        config = AgentConfig()
    except ValueError as e:
        pytest.skip(f"Skipping test due to missing API Keys: {e}")

    if config.active_provider != "openrouter":
        pytest.skip("Skipping OpenRouter E2E test: OPENROUTER_API_KEY is missing or not active.")

    api_key = config.active_api_key
    provider = config.active_provider

    # Initialize the tool
    image_classifier = ImageClassifier(
        api_key=api_key,
        provider=provider,
        model="openai/gpt-4o-mini"
    )

    # Use existing test image
    image_path = Path(__file__).parent / "challenge_view" / "image_label_binary" / "1.png"
    assert image_path.exists(), f"Test image not found at {image_path}"

    # Perform inference
    result = await image_classifier(challenge_screenshot=image_path)

    # Validate output structure
    assert isinstance(result, ImageBinaryChallenge), "Result must be a Pydantic ImageBinaryChallenge object"
    assert isinstance(result.coordinates, list), "Result.coordinates should be a list"
    
    # Check that coordinates contain items
    if result.coordinates:
        assert hasattr(result.coordinates[0], "box_2d"), "Each coordinate should have a box_2d"
