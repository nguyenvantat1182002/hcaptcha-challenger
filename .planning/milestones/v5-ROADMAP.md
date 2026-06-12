# Milestone 5: Relative Coordinate System

*Normalize coordinate grid images to start from 0 for LLM inferences to improve accuracy and consistency.*

## Phases

### Phase 9: Grid Normalization and Translation
- Update coordinate grid image generation to render relative axes `[0-W, 0-H]`.
- Refactor `RoboticArm` to translate returned relative coordinates back to absolute page coordinates before executing clicks and drags.
