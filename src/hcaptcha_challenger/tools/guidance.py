import json
from pathlib import Path
from typing import Optional
import threading
from filelock import FileLock
from loguru import logger
from pydantic import BaseModel, Field

from hcaptcha_challenger.models import ChallengeTypeEnum
from hcaptcha_challenger.tools.internal.providers.openrouter import OpenRouterProvider

class GuidanceResponse(BaseModel):
    guidance: str = Field(..., description="The concise solution path and objects to look for")


class GuidanceManager:
    """
    Manages the dynamic generation of instructions (guidance) for solver models using a multimodal LLM.
    Results are cached in a JSON file to minimize redundant API calls.
    """

    def __init__(self, openrouter_api_key: str, model: str, cache_file: Path, verify_ssl: bool = True, timeout: float = 120.0):
        self.api_key = openrouter_api_key
        self.model = model
        self.cache_file = cache_file
        self.timeout = timeout
        self.lock_file = cache_file.with_suffix(".lock")
        self.memory_lock = threading.Lock()
        self.provider = OpenRouterProvider(api_key=openrouter_api_key, model=model, verify_ssl=verify_ssl)
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load guidance cache: {e}")
        return {}

    def _save_cache(self):
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with FileLock(self.lock_file, timeout=10):
                # Reload right before saving to prevent overwriting other processes' updates
                current_cache = self._load_cache()
                current_cache.update(self.cache)
                self.cache_file.write_text(json.dumps(current_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save guidance cache: {e}")

    def get_guidance(self, challenge_prompt: str, challenge_screenshot: Path, job_type: ChallengeTypeEnum) -> str:
        with self.memory_lock:
            # Check file cache in case another process/thread updated it
            self.cache.update(self._load_cache())
            
            if challenge_prompt in self.cache:
                logger.debug(f"Guidance cache hit for prompt: {challenge_prompt}")
                cached_item = self.cache[challenge_prompt]
                if isinstance(cached_item, dict) and "guidance" in cached_item:
                    return cached_item["guidance"]
                elif isinstance(cached_item, str):
                    # Legacy migration
                    self.cache[challenge_prompt] = {"guidance": cached_item, "failures": 0}
                    self._save_cache()
                    return cached_item

        logger.info(f"Generating new guidance for prompt: {challenge_prompt}")
        description = (
            "You are an expert AI assistant guiding a vision model to solve visual challenges. "
            "Analyze the sample image and the provided question to understand the requested object. "
            "IMPORTANT: Your guidance MUST be general and conceptual. Describe the visual characteristics "
            "(shape, color, category, distinguishing features) of the target objects so the solver model "
            "can find them in ANY future image with the same question. DO NOT mention specific locations "
            "(like 'top-left') or specific details unique to this one sample image."
        )
        
        user_prompt = f"Question: {challenge_prompt}\nChallenge Type: {job_type.value}"
        
        try:
            response = self.provider.generate_with_images(
                images=[challenge_screenshot],
                response_schema=GuidanceResponse,
                user_prompt=user_prompt,
                description=description,
                timeout=self.timeout
            )
            guidance_str = response.guidance
            with self.memory_lock:
                self.cache[challenge_prompt] = {"guidance": guidance_str, "failures": 0}
            self._save_cache()
            return guidance_str
        except Exception as e:
            logger.error(f"Failed to generate guidance: {e}")
            return f"Please note that the current task type is: {job_type.value}"

    def clear_guidance(self, challenge_prompt: str):
        """
        Removes a guidance from both memory and file cache. 
        Useful for self-healing when a guidance is proven ineffective.
        """
        with self.memory_lock:
            if challenge_prompt in self.cache:
                self.cache.pop(challenge_prompt)
                logger.info(f"Cleared bad guidance from memory for prompt: {challenge_prompt}")
            
            try:
                with FileLock(self.lock_file, timeout=10):
                    file_cache = self._load_cache()
                    if challenge_prompt in file_cache:
                        file_cache.pop(challenge_prompt)
                        self.cache_file.write_text(json.dumps(file_cache, ensure_ascii=False, indent=2), encoding="utf-8")
                        logger.info(f"Cleared bad guidance from file cache for prompt: {challenge_prompt}")
            except Exception as e:
                logger.warning(f"Failed to clear guidance from cache file: {e}")

    def record_failure(self, challenge_prompt: str, max_failures: int = 3):
        needs_clear = False
        with self.memory_lock:
            self.cache.update(self._load_cache())
            cached_item = self.cache.get(challenge_prompt)
            if isinstance(cached_item, str):
                cached_item = {"guidance": cached_item, "failures": 0}
            if isinstance(cached_item, dict):
                cached_item["failures"] = cached_item.get("failures", 0) + 1
                failures = cached_item["failures"]
                logger.debug(f"Guidance failure recorded for '{challenge_prompt}': {failures}/{max_failures}")
                self.cache[challenge_prompt] = cached_item
                self._save_cache()
                if failures >= max_failures:
                    needs_clear = True
        
        if needs_clear:
            logger.warning(f"Guidance max failures reached ({max_failures}) for '{challenge_prompt}', clearing guidance.")
            self.clear_guidance(challenge_prompt)

    def record_success(self, challenge_prompt: str):
        # Theo yêu cầu code review, khi giải đúng thì KHÔNG ép failures về 0 nữa.
        # Điều này sẽ khiến failure count mang tính chất cộng dồn (cumulative) thay vì liên tiếp (consecutive).
        pass
