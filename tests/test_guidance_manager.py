import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from hcaptcha_challenger.tools.guidance import GuidanceManager, GuidanceResponse
from hcaptcha_challenger.models import ChallengeTypeEnum

@pytest.fixture
def temp_cache_file(tmp_path):
    return tmp_path / "guidance_cache.json"

def test_guidance_manager_caching(temp_cache_file):
    # Mock the OpenRouterProvider
    with patch("hcaptcha_challenger.tools.guidance.OpenRouterProvider") as mock_provider_cls:
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider
        
        # Mock the generation response
        mock_response = GuidanceResponse(guidance="Cái tủ, ghế")
        mock_provider.generate_with_images.return_value = mock_response
        
        manager = GuidanceManager("dummy_key", "dummy_model", temp_cache_file)
        
        prompt = "Chọn các đồ vật được làm từ con người"
        screenshot = Path("dummy.png")
        
        # First call should hit the provider
        guidance = manager.get_guidance(prompt, screenshot, ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT)
        assert guidance == "Cái tủ, ghế"
        mock_provider.generate_with_images.assert_called_once()
        
        # Verify JSON cache was written
        assert temp_cache_file.exists()
        import json
        cache_data = json.loads(temp_cache_file.read_text(encoding="utf-8"))
        assert cache_data[prompt] == "Cái tủ, ghế"
        
        # Second call should hit the cache, not the provider
        guidance2 = manager.get_guidance(prompt, screenshot, ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT)
        assert guidance2 == "Cái tủ, ghế"
        assert mock_provider.generate_with_images.call_count == 1
