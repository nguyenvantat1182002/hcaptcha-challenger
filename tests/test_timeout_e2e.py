import os
import pytest
from pathlib import Path
import httpx
import openai
from dotenv import load_dotenv
from hcaptcha_challenger.tools import ImageClassifier

load_dotenv()

@pytest.mark.asyncio
async def test_llm_timeout_exception(tmp_path: Path):
    """
    Test that an extremely low LLM_TIMEOUT triggers a timeout exception 
    when making a request to OpenRouter. This verifies that the timeout configuration
    is correctly passed down to the HTTP client layer.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set. Skipping timeout test.")

    # Instantiate the classifier with a ridiculously low timeout (10 milliseconds)
    classifier = ImageClassifier(
        api_key=api_key,
        provider="openrouter",
        timeout=0.01  # 10ms timeout should always fail
    )

    # Create a dummy image for testing
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")

    with pytest.raises((httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException, openai.APITimeoutError)):
        await classifier(challenge_screenshot=dummy_img)

@pytest.mark.asyncio
async def test_llm_timeout_exception_gemini(tmp_path: Path):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set. Skipping timeout test.")

    # Instantiate the classifier with a ridiculously low timeout (10 milliseconds)
    classifier = ImageClassifier(
        api_key=api_key,
        provider="gemini",
        timeout=0.01  # 10ms timeout should always fail
    )

    dummy_img = tmp_path / "dummy_gemini.png"
    dummy_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")

    import google.genai.errors
    with pytest.raises((httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException, google.genai.errors.APIError, Exception)):
        await classifier(challenge_screenshot=dummy_img)
