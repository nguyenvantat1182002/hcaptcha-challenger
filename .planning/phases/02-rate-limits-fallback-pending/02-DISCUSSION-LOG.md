# Discussion Log: Phase 2

## Vùng xám đã thảo luận
1. **Fallback Models Configuration**
   - Lựa chọn: Lấy danh sách fallback mặc định từ biến môi trường `OPENROUTER_FALLBACK_MODELS`. Cho phép ghi đè cấu hình này thông qua tham số hàm khi gọi API để tăng tính linh hoạt.

2. **Handling Rate Limits (429)**
   - Lựa chọn: Tính toán thời gian không cho xảy ra 429 thông qua API kiểm tra giới hạn của OpenRouter để ngăn chặn lỗi 429 một cách chủ động, thay vì chỉ dựa vào Exponential Backoff mù quáng.

## Ghi chú của hệ thống
- Các quyết định này ảnh hưởng đến việc xử lý lỗi (Resiliency) trong quá trình gọi API, sẽ được cung cấp làm đầu vào cho planner ở bước tiếp theo.
