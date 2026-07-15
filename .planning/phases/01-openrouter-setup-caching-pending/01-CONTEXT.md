# Context: Phase 1

## Domain
OpenRouter Setup & Caching — Khởi tạo client gọi OpenRouter và tích hợp `provider-sticky-routing` để tối ưu chi phí thông qua Prompt Caching.

## Decisions
- **Sticky Routing Configuration**: Sẽ hardcode tùy chọn `provider-sticky-routing=true` trực tiếp vào `extra_headers` của tất cả các request OpenRouter để tự động hưởng lợi từ Prompt Caching. (Được uỷ quyền quyết định).
- **Explicit Caching**: Không cần thiết lập tham số `prompt-cache-options` riêng lẻ, chỉ cần dựa vào cơ chế sticky routing của OpenRouter.
- **Model String**: Vẫn duy trì cơ chế truyền model identifier linh hoạt thông qua tham số `model` của hàm tạo (ví dụ `openai/gpt-4o-mini`).

## Canonical Refs
- `.planning/ROADMAP.md`

## Deferred Ideas
- Đưa tính năng Sticky Routing vào cấu hình môi trường (ví dụ `.env` / Pydantic Settings) để người dùng có thể tắt khi cần ưu tiên tính sẵn sàng (Failover) hơn là tính kinh tế (Caching).
