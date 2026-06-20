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
from hcaptcha_challenger.models import RequestType, ChallengeTypeEnum

class SolverService:
    def __init__(self):
        logger.info("Initializing SolverService and AI Reasoners...")
        self.config = AgentConfig()
        
        self.router = ChallengeRouter(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.CHALLENGE_CLASSIFIER_MODEL,
            timeout=self.config.LLM_TIMEOUT,
        )
        
        self.image_classifier = ImageClassifier(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.IMAGE_CLASSIFIER_MODEL,
            timeout=self.config.LLM_TIMEOUT,
        )
        
        self.point_reasoner = SpatialPointReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SPATIAL_POINT_REASONER_MODEL,
            timeout=self.config.LLM_TIMEOUT,
        )
        
        self.path_reasoner = SpatialPathReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SPATIAL_PATH_REASONER_MODEL,
            timeout=self.config.LLM_TIMEOUT,
        )
        logger.info("AI Reasoners initialized successfully.")

    def _generate_grid_divisions(self, image_path: Path) -> Path:
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
        
        fd, grid_path = tempfile.mkstemp(suffix="_grid.png")
        os.close(fd)
        
        plt.imsave(grid_path, result_img)
        return Path(grid_path)

    async def solve_challenge(self, prompt: str, image_b64: str) -> List[Dict[str, int]]:
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
            
            # Determine the challenge type using the router
            logger.debug(f"Routing challenge for prompt: '{prompt}'")
            router_result = await self.router(challenge_screenshot=temp_file_path)
            challenge_type = router_result.challenge_type
            logger.info(f"Detected challenge type: {challenge_type}")
            
            # Dispatch to appropriate tool
            if challenge_type in (RequestType.IMAGE_LABEL_BINARY, "image_label_binary"):
                logger.debug("Dispatching to ImageClassifier")
                response = await self.image_classifier(
                    challenge_screenshot=temp_file_path,
                    auxiliary_information=prompt
                )
                
                # ImageBinaryChallenge returns `coordinates: List[BoundingBoxCoordinate]`
                return [{"x": coord.box_2d[0], "y": coord.box_2d[1]} for coord in response.coordinates]
                
            elif challenge_type in (
                ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
                ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT,
                RequestType.IMAGE_LABEL_AREA_SELECT,
                "image_label_single_select",
                "image_label_multi_select"
            ):
                logger.debug("Dispatching to SpatialPointReasoner")
                grid_path = self._generate_grid_divisions(temp_file_path)
                try:
                    response = await self.point_reasoner(
                        challenge_screenshot=temp_file_path,
                        grid_divisions=grid_path,
                        auxiliary_information=prompt
                    )
                    
                    # ImageAreaSelectChallenge returns `points: List[PointCoordinate]`
                    return [{"x": point.x, "y": point.y} for point in response.points]
                finally:
                    if os.path.exists(grid_path):
                        os.remove(grid_path)
                
            elif challenge_type in (
                ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
                ChallengeTypeEnum.IMAGE_DRAG_MULTI,
                RequestType.IMAGE_DRAG_DROP,
                "image_drag_single",
                "image_drag_multi"
            ):
                logger.debug("Dispatching to SpatialPathReasoner")
                grid_path = self._generate_grid_divisions(temp_file_path)
                try:
                    response = await self.path_reasoner(
                        challenge_screenshot=temp_file_path,
                        grid_divisions=grid_path,
                        auxiliary_information=prompt
                    )
                    
                    # ImageDragDropChallenge returns `paths: List[SpatialPath]`
                    result = []
                    for path in response.paths:
                        result.append({
                            "from": {"x": path.start_point.x, "y": path.start_point.y},
                            "to": {"x": path.end_point.x, "y": path.end_point.y}
                        })
                    return result
                finally:
                    if os.path.exists(grid_path):
                        os.remove(grid_path)
            else:
                logger.warning(f"Unsupported challenge type detected: {challenge_type}")
                return []
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

# Global singleton instance
solver_service = None

def get_solver_service() -> SolverService:
    global solver_service
    if solver_service is None:
        solver_service = SolverService()
    return solver_service
