import pytest
from hcaptcha_challenger.tools.internal.providers.openrouter.provider import OpenRouterProvider

@pytest.mark.asyncio
async def test_openrouter_provider_sticky_routing_header_injected():
    # Initialize provider with dummy API key to bypass remote validation
    provider = OpenRouterProvider(api_key="sk-or-v1-dummy", model="openai/gpt-4o-mini")
    
    # Get the underlying AsyncOpenAI client
    client = provider.client
    
    # Verify that default_headers contains the provider-sticky-routing header
    assert "provider-sticky-routing" in client.default_headers, "provider-sticky-routing header is missing"
    assert client.default_headers["provider-sticky-routing"] == "true", "provider-sticky-routing header value should be 'true'"
