# Requirements: Spatial Reasoning V2

## Features

### MUST-HAVE
- **Explicit Grid Labeling**: Numerical labels on the X and Y axes visible to the LLM.
- **Systematic Reasoning Prompt**: A "Cell Identification" step in the spatial tool prompts.
- **Standardized Coordinate Response**: Ensure all spatial tools return a machine-parseable JSON format (as defined in `models.py`).

### SHOULD-HAVE
- **Banded Contrast Grid**: Subtly contrasting cells to avoid visual cell drifting.
- **Benchmarking Tools**: Scripts to capture and verify the accuracy of spatial reasoning across different challenges.

### COULD-HAVE
- **Local Zoom Step**: Auto-cropping and re-reasoning on ambiguous objects.
- **Confidence Scoring**: Ability for LLM to signal "uncertainty" in spatial mapping.

## Non-Functional
- **Performance**: Grid generation must be under 300ms.
- **Cost**: Minimize tokens by avoiding excessive CoT in the prompt where not needed.
- **Stability**: Works across different screen resolutions and DPIs in Camoufox.

## Verification / UAT
- [ ] LLM selects object with < 5% error margin on a 500x500 image.
- [ ] No "Unknown request_type" errors on invisible challenges.
- [ ] Successfully solves 3 consecutive "Area Selection" challenges in Riot Games flow.

---
*Last updated: 2026-04-05 after initialization*
