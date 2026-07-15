# Context: Phase 2

## Domain
Rate Limits & Fallback — Cập nhật logic xử lý lỗi 429 và truyền cấu hình dự phòng (fallback) qua OpenRouter.

## Decisions
- **Fallback Models Configuration**: Lấy danh sách fallback mặc định từ biến môi trường `OPENROUTER_FALLBACK_MODELS`. Cho phép ghi đè cấu hình này thông qua tham số hàm khi gọi API để tăng tính linh hoạt.
- **Handling Rate Limits (429) & 70% Threshold (API Based)**: Theo yêu cầu của người dùng, bất chấp việc OpenRouter đánh dấu là deprecated, hệ thống **vẫn sẽ sử dụng API `GET /api/v1/auth/key`** để lấy thông tin Rate Limits. Logic được thiết kế như sau: Hệ thống sẽ phân tích cú pháp (parse) kết quả từ API này. Nếu xác định được mức độ sử dụng đạt **ngưỡng 70%**, hệ thống sẽ tính toán thời gian chờ, **lưu thời gian reset ra file tạm `.openrouter_ratelimit`**. Mọi tiến trình trước khi gửi request tới model đều sẽ đọc file này; nếu còn hiệu lực thì chủ động `sleep` để tránh 429.

## Canonical Refs
- `.planning/ROADMAP.md`

## Deferred Ideas
- (Không có)
