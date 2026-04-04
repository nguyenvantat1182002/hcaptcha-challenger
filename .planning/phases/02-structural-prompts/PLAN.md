# Phase 2 Plan: Structural Prompt Engineering (CoT-Spatial)

## Overview
This phase implements the "Geometric Description" Chain-of-Thought (CoT) method to improve the accuracy of spatial reasoning. LLMs will be guided to describe the object's position relative to the grid before providing coordinates.

---

## Task 1: Update GeminiProvider for CoT Support
**Goal**: Allow LLMs to output reasoning text *before* the structured JSON result.
- [ ] Modify `src/hcaptcha_challenger/tools/internal/providers/gemini.py`.
- [ ] Update `generate_with_images` to make `response_schema` and `"application/json"` optional base on a flag.
- [ ] Ensure that if `response_schema` is omitted, the model can output a free-text reasoning section followed by a JSON code block.

## Task 2: Refactor Spatial Reasoner Prompts
**Goal**: Implement the "Geometric Description" CoT in all spatial reasoners.
- [ ] Update `src/hcaptcha_challenger/tools/spatial/point.md`.
- [ ] Update `src/hcaptcha_challenger/tools/spatial/path.md`.
- [ ] Update `src/hcaptcha_challenger/tools/spatial/bbox.md`.
- [ ] New prompt structure: 
  - (1) Identify object.
  - (2) Identify grid coordinate range (X=[...], Y=[...]).
  - (3) Describe relative position within that cell.
  - (4) Provide target coordinate.
  - (5) Output final JSON.

## Task 3: Regression Test for Coordinate Extraction
**Goal**: Verify that the changes do not break existing captcha solving flows.
- [ ] Test with `examples/demo_camoufox.py` on complex hCaptcha tasks.
- [ ] Verify that `extract_first_json_block` successfully parses the response even with preceding text.

## Verification Checklist
- [ ] Gemini logs show the "Geometric Reasoning" thought process before the "LLM Usage" log.
- [ ] Final (x, y) coordinates match the visual center of correctly identified objects.
- [ ] No `ValidationError` occurs when parsing the JSON block into Pydantic models.

---
*Created: 2026-04-05 during Phase 2 Planning*
