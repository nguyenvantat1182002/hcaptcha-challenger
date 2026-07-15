# Architecture

**Date:** 2026-07-16
**Scope:** Core Application

## Core Patterns
- **Agentic Workflow**: Uses Multimodal LLMs and computer vision to solve hCaptcha.
- **Pluggable Resources**: Employs a strategy pattern to swap in different models (ResNet, YOLOv8, ViT, LLMs) depending on the challenge type (image label, bounding box, drag & drop).
- **Browser Automation**: Interacts with the web page directly using `playwright` or `camoufox` to bypass bot detection without relying on browser extensions.

## Data Flow
1. **Challenge Detection**: Agent detects hCaptcha widget on the page.
2. **Task Parsing**: Classifies the type of challenge (e.g., `image_label_binary`, `image_drag_drop`).
3. **Inference / Solution**:
   - For classification, calls local ONNX models (ResNet) or LLMs.
   - For object detection, uses YOLOv8.
   - For logic/spatial tasks, routes to Multimodal LLMs (Gemini/OpenAI).
4. **Action Execution**: Emulates human-like mouse movements/clicks to interact with the challenge interface.
5. **Verification**: Checks if the challenge was successfully passed or if a retry is needed.
