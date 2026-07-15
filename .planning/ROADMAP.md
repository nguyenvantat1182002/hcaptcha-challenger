# Roadmap

**Goal:** Triển khai OpenRouter Prompt Caching & Rate Limits (hCaptcha Challenger)

## Phase 1: OpenRouter Setup & Caching [Pending]
- **Goal**: Khởi tạo client gọi OpenRouter và tích hợp `provider-sticky-routing`.
- **Requirements**: OR-01, OR-02
- **Milestone**: Request lên OpenRouter chạy ổn định và giữ được cache state.

## Phase 2: Rate Limits & Fallback [Pending]
- **Goal**: Cập nhật logic retry để dùng Exponential Backoff xử lý lỗi 429 và truyền cấu hình Fallback.
- **Requirements**: RES-01, RES-02
- **Milestone**: Hệ thống tự động phục hồi an toàn (qua retry hoặc fallback models) khi gặp lỗi 429 từ nền tảng hoặc upstream.
