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
        assert cache_data[prompt]["guidance"] == "Cái tủ, ghế"
        
        # Second call should hit the cache, not the provider
        guidance2 = manager.get_guidance(prompt, screenshot, ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT)
        assert guidance2 == "Cái tủ, ghế"
        assert mock_provider.generate_with_images.call_count == 1

def test_guidance_manager_failure_tracking(temp_cache_file):
    manager = GuidanceManager("dummy_key", "dummy_model", temp_cache_file)
    prompt = "Please select all apples."
    
    # Initialize cache manually to test increment logic
    manager.cache[prompt] = {"guidance": "Select the red fruits", "failures": 0}
    manager._save_cache()
    
    # Test record_failure
    manager.record_failure(prompt, max_failures=3)
    data = manager._load_cache()
    assert data[prompt]["failures"] == 1
    
    manager.record_failure(prompt, max_failures=3)
    data = manager._load_cache()
    assert data[prompt]["failures"] == 2
    
    # Test record_success no longer resets failures
    manager.record_success(prompt)
    data = manager._load_cache()
    assert data[prompt]["failures"] == 2
    
    # Test reaching threshold (only 1 more needed to reach 3)
    manager.record_failure(prompt, max_failures=3)
    
    data = manager._load_cache()
    assert prompt not in data

