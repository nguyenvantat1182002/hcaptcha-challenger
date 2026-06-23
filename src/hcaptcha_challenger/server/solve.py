import os
import base64
import tempfile
from pathlib import Path
from typing import List, Dict

from loguru import logger

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.tools import (
    ChallengeRouter,
    ImageClassifier,
    SpatialPointReasoner,
    SpatialPathReasoner,
)
from hcaptcha_challenger.tools.supervisor import SupervisorReasoner, SupervisorCache
from hcaptcha_challenger.models import RequestType, ChallengeTypeEnum
import asyncio

class SolverService:
    def __init__(self, timeout: float | None = None):
        logger.info("Initializing SolverService and AI Reasoners...")
        self.config = AgentConfig()
        
        llm_timeout = float(timeout) if timeout is not None else self.config.LLM_TIMEOUT
        
        self.router = ChallengeRouter(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.CHALLENGE_CLASSIFIER_MODEL,
            timeout=llm_timeout,
        )
        
        self.image_classifier = ImageClassifier(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.IMAGE_CLASSIFIER_MODEL,
            timeout=llm_timeout,
        )
        
        self.point_reasoner = SpatialPointReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SPATIAL_POINT_REASONER_MODEL,
            timeout=llm_timeout,
        )
        
        self.path_reasoner = SpatialPathReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SPATIAL_PATH_REASONER_MODEL,
            timeout=llm_timeout,
        )
        
        self.supervisor_reasoner = SupervisorReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SUPERVISOR_MODEL,
            timeout=llm_timeout,
        )
        self.supervisor_cache = SupervisorCache(
            cache_file=Path(self.config.cache_dir, "supervisor_guidelines.json"),
            invalidation_threshold=self.config.SUPERVISOR_INVALIDATION_THRESHOLD,
            enable_regeneration=self.config.ENABLE_GUIDANCE_REGENERATION,
        )
        logger.info("AI Reasoners initialized successfully.")

    def _generate_grid_divisions(self, image_path: Path, cache_key: Path) -> Path:
        import cv2
        import matplotlib.pyplot as plt
        from hcaptcha_challenger.helper import create_coordinate_grid
        
        img = cv2.imread(str(image_path))
        height, width = img.shape[:2]
        bbox = {"x": 0, "y": 0, "width": width, "height": height}
        
        result_img = create_coordinate_grid(
            image=image_path,
            bbox=bbox,
            x_line_space_num=self.config.coordinate_grid.x_line_space_num,
            y_line_space_num=self.config.coordinate_grid.y_line_space_num,
            adaptive_contrast=self.config.coordinate_grid.adaptive_contrast,
            color=self.config.coordinate_grid.color,
        )
        
        grid_path = cache_key / f"{cache_key.name}_grid.png"
        plt.imsave(grid_path, result_img)
        return grid_path

    async def _get_or_generate_guideline(self, challenge_prompt: str, challenge_screenshot: Path) -> str:
        if not self.config.ENABLE_SUPERVISOR:
            return ""

        cached_guideline = self.supervisor_cache.get_guideline(challenge_prompt)
        if cached_guideline:
            return cached_guideline

        try:
            guideline = await self.supervisor_reasoner(
                challenge_prompt=challenge_prompt,
                challenge_screenshot=challenge_screenshot,
            )
            if guideline:
                self.supervisor_cache.save_guideline(challenge_prompt, guideline)
            return guideline
        except Exception as e:
            logger.error(f"Failed to generate supervisor guideline: {e}")
            return "Please follow the standard rules for this challenge."

    async def solve_challenge(
        self, 
        prompt: str, 
        image_b64: str, 
        challenge_type: str = None
    ) -> List[Dict[str, int]]:
        """
        Processes a challenge with base64 image and prompt.
        Returns a list of coordinates or path dictionaries.
        """
        # Save base64 to temp file
        img_data = base64.b64decode(image_b64)
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(img_data)
            
            temp_file_path = Path(temp_path)
            
            # Determine the challenge type if not provided
            if challenge_type is None:
                logger.debug(f"Routing challenge for prompt: '{prompt}'")
                router_result = await self.router(challenge_screenshot=temp_file_path)
                challenge_type = router_result.challenge_type
            logger.info(f"Detected challenge type: {challenge_type}")
            
            # Create persistent cache structure
            cache_key = self.config.create_cache_key(
                request_type=str(challenge_type),
                prompt=prompt
            )
            cache_key.mkdir(parents=True, exist_ok=True)
            cache_img_path = cache_key / f"{cache_key.name}_raw.png"
            
            import shutil
            shutil.move(str(temp_file_path), str(cache_img_path))
            
            logger.info(f"Challenge cache initialized at: {cache_key}")
            
            # Generate Supervisor Guideline
            guideline = await self._get_or_generate_guideline(prompt, cache_img_path)
            enhanced_prompt = f"{prompt}\n\n## SUPERVISOR GUIDANCE\n{guideline}" if guideline else prompt
            
            # Dispatch to appropriate tool
            if challenge_type in (RequestType.IMAGE_LABEL_BINARY, "image_label_binary"):
                logger.debug("Dispatching to ImageClassifier")
                response = await self.image_classifier(
                    challenge_screenshot=cache_img_path,
                    auxiliary_information=enhanced_prompt
                )
                self.image_classifier.cache_response(
                    path=cache_key / f"{cache_key.name}_model_answer.json"
                )
                
                # ImageBinaryChallenge returns `coordinates: List[BoundingBoxCoordinate]`
                return [{"box_2d": [coord.box_2d[0], coord.box_2d[1]]} for coord in response.coordinates]
                
            elif challenge_type in (
                ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
                ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT,
                RequestType.IMAGE_LABEL_AREA_SELECT,
                "image_label_single_select",
                "image_label_multi_select"
            ):
                logger.debug("Dispatching to SpatialPointReasoner")
                grid_path = self._generate_grid_divisions(cache_img_path, cache_key)
                response = await self.point_reasoner(
                    challenge_screenshot=cache_img_path,
                    grid_divisions=grid_path,
                    auxiliary_information=enhanced_prompt
                )
                self.point_reasoner.cache_response(
                    path=cache_key / f"{cache_key.name}_model_answer.json"
                )
                
                # ImageAreaSelectChallenge returns `points: List[PointCoordinate]`
                return [{"x": point.x, "y": point.y} for point in response.points]
                
            elif challenge_type in (
                ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
                ChallengeTypeEnum.IMAGE_DRAG_MULTI,
                RequestType.IMAGE_DRAG_DROP,
                "image_drag_single",
                "image_drag_multi"
            ):
                logger.debug("Dispatching to SpatialPathReasoner")
                grid_path = self._generate_grid_divisions(cache_img_path, cache_key)
                response = await self.path_reasoner(
                    challenge_screenshot=cache_img_path,
                    grid_divisions=grid_path,
                    auxiliary_information=enhanced_prompt
                )
                self.path_reasoner.cache_response(
                    path=cache_key / f"{cache_key.name}_model_answer.json"
                )
                
                # ImageDragDropChallenge returns `paths: List[SpatialPath]`
                result = []
                for path in response.paths:
                    result.append({
                        "from": {"x": path.start_point.x, "y": path.start_point.y},
                        "to": {"x": path.end_point.x, "y": path.end_point.y}
                    })
                return result
            else:
                logger.warning(f"Unsupported challenge type detected: {challenge_type}")
                return []
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
