# Concerns

## Technical Debt & Maintenance
- **LLM Dependency**: The core capability relies heavily on Google GenAI models. Any changes to API availability, rate limits, latency, or model accuracy will directly impact the tool's effectiveness.
- **Browser Fingerprinting**: Ensuring stealthy browser automation (`playwright`, `camoufox`) is an ongoing battle. hCaptcha regularly updates its bot detection mechanisms, requiring constant monitoring and updates to the stealth configurations.

## Known Complex Areas
- **Spatial Reasoning Prompts**: Designing and maintaining prompts for multimodal LLMs to accurately perform spatial reasoning (bounding boxes, precise point selection) is complex and non-deterministic.
- **DOM Stability**: Captcha challenges often change their DOM structure or internal logic without notice, which can break the `agent`'s observation and interaction phases.

*(Note: The `archive` component has been explicitly excluded from this map.)*
