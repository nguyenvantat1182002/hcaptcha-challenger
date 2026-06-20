# Concerns & Known Issues

## Technical Risks
- **Bot Mitigation Changes**: hCaptcha frequently updates its detection mechanisms. The project heavily relies on browser masking (Camoufox) and Playwright; upstream changes could break the flow.
- **LLM Latency & Cost**: Using Multimodal LLMs introduces variability in execution time and potential API costs, especially under heavy load.
- **Vision Reliability**: LLMs are known to struggle with precise coordinate mapping on images, which is why intermediate CV tools are used. Keeping the synergy between CV grid-making and LLM prompt accuracy is an ongoing challenge.

## Maintenance Items
- Managing multiple supported LLM providers means adapting to different API schemas and rate limits.
- E2E tests can be flaky if they rely on live CAPTCHA challenges or external LLM providers.
