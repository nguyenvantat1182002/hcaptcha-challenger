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
            if challenge_prompt in self.cache:
                logger.debug(f"Guidance memory cache hit for prompt: {challenge_prompt}")
                return self.cache[challenge_prompt]
            
            # Check file cache in case another process/thread updated it
            file_cache = self._load_cache()
            if challenge_prompt in file_cache:
                self.cache.update(file_cache)
                logger.debug(f"Guidance file cache hit for prompt: {challenge_prompt}")
                return self.cache[challenge_prompt]

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
                self.cache[challenge_prompt] = guidance_str
            self._save_cache()
            return guidance_str
        except Exception as e:
            logger.error(f"Failed to generate guidance: {e}")
            return f"Please note that the current task type is: {job_type.value}"
