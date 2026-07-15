# hCaptcha Challenger

A multimodal agentic workflow tool that bypasses hCaptcha challenges using local computer vision models and remote Large Language Models (LLMs) without relying on browser extensions or external third-party anti-captcha services.

## Core Value

Gracefully and reliably solving complex hCaptcha challenges using "AI vs AI" strategies while maintaining a high bypass rate and remaining undetected by anti-bot measures.

## Requirements

### Validated

- ✓ Browser automation & anti-detection via Playwright and Camoufox — existing
- ✓ Solving challenges via pluggable local vision models (ResNet, YOLOv8) — existing
- ✓ Base LLM integrations for logic and spatial reasoning (Google Gemini, OpenAI) — existing

### Active

- [ ] Tích hợp nền tảng OpenRouter cho LLM Providers
- [ ] Áp dụng Prompt Caching với header `provider-sticky-routing` trên OpenRouter để tối ưu chi phí
- [ ] Xử lý hiệu quả Rate Limits (Lỗi HTTP 429) thông qua Exponential Backoff
- [ ] Áp dụng Fallback Routing để dự phòng khi provider gốc báo lỗi (dựa trên `provider_code`)

### Out of Scope

- Loại bỏ hoàn toàn local models — Lý do: Cần duy trì local models (ResNet, YOLO) cho các tác vụ phân loại cơ bản (binary label) nhằm tối ưu tốc độ và chi phí thay vì gọi LLM.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Kích hoạt `provider-sticky-routing` | Theo tài liệu LLM Wiki, tính năng này ép request vào một provider cố định để duy trì trạng thái "warm" của cache, tối đa hóa Prompt Caching. | — Pending |
| Đổi Retry sang Exponential Backoff | Tránh spam request gây chặn IP hoặc block account khi hệ thống Cloudflare của OpenRouter (hoặc Upstream Provider) trả về lỗi 429 (Too Many Requests). | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-16 after initialization*
