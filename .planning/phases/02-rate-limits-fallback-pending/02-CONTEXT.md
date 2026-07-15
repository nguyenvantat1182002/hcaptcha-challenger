# Context: Phase 2

## Domain
Rate Limits & Fallback — Cập nhật logic xử lý lỗi 429 và truyền cấu hình dự phòng (fallback) qua OpenRouter.

## Decisions
- **Fallback Models Configuration**: Lấy danh sách fallback mặc định từ biến môi trường `OPENROUTER_FALLBACK_MODELS`. Cho phép ghi đè cấu hình này thông qua tham số hàm khi gọi API để tăng tính linh hoạt.
- **Handling Rate Limits (429)**: Sử dụng trực tiếp API kiểm tra giới hạn (Rate Limits) của OpenRouter để tính toán chính xác thời gian được phép gọi tiếp theo, nhằm chủ động ngăn chặn lỗi 429 (hoặc dùng để xác định thời gian chờ chính xác) thay vì chỉ dựa vào Exponential Backoff tiêu chuẩn.

## Canonical Refs
- `.planning/ROADMAP.md`

## Deferred Ideas
- (Không có)
