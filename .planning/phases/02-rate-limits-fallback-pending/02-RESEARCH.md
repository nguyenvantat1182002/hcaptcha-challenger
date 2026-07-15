# Research: Phase 2 - Rate Limits & Fallback (API Based)

## 1. Domain
Rate Limits & Fallback trong `hcaptcha_challenger` sử dụng OpenRouter provider.

## 2. Context & Constraints
- Dựa theo `02-CONTEXT.md`, yêu cầu bắt buộc là sử dụng API `GET https://openrouter.ai/api/v1/auth/key` để lấy thông tin Rate Limits.
- Nếu giới hạn chạm ngưỡng 70% (`limit_remaining` <= `limit` * 0.3 hoặc một field tương đương), hệ thống sẽ chủ động lấy thời gian `reset`.
- Thông tin thời gian `reset` sẽ được lưu ra một file IPC (`.openrouter_ratelimit`) để đồng bộ trạng thái đa tiến trình (tránh 429).
- Mọi tiến trình trước khi gọi API phải đọc file này và `sleep` nếu cần.

## 3. Phân tích Kỹ thuật
### 3.1. API `/auth/key` của OpenRouter
- Endpoint: `https://openrouter.ai/api/v1/auth/key`
- Method: `GET`
- Header: `Authorization: Bearer <OPENROUTER_API_KEY>`
- Theo thực nghiệm từ curl, endpoint này trả về:
  ```json
  {
    "data": {
      "limit": null,
      "limit_remaining": null,
      "usage": 0.003,
      "rate_limit": {
        "requests": -1,
        "interval": "10s",
        "note": "This field is deprecated..."
      }
    }
  }
  ```
- **Rủi ro kỹ thuật**: OpenRouter hiện trả về `limit=null` và `rate_limit.requests=-1` cho đa số các key thông thường (trừ key có giới hạn chi tiêu hard limit). Do vậy, việc tính "70%" theo API này ở trạng thái hiện tại sẽ gặp khó khăn vì `limit` không xác định.
- **Giải pháp xử lý (Fallback Logic)**: 
  - Gửi request đến API `/auth/key`. 
  - Nếu `rate_limit` (hoặc `limit`) tồn tại hợp lệ (không phải `null`, > 0): tính toán 70%.
  - Nếu `limit` là `null` hoặc `-1`: ta sẽ dựa vào các request fail `RateLimitError` 429 thực tế. Khi bắt được 429, ta xem như đã dùng 100%, ghi đè file `.openrouter_ratelimit` với một khoảng thời gian backoff nhất định (ví dụ: 10s hoặc lấy từ header `x-ratelimit-reset` của exception nếu có).

### 3.2. Quản lý IPC File (`.openrouter_ratelimit`)
- File được dùng như một khoá đồng bộ trạng thái đơn giản (Lock/Semaphore).
- Chứa nội dung là Epoch time: `1700000000.123` (thời điểm reset).
- Khi hàm `generate_with_images` bắt đầu: đọc nội dung file.
  - Nếu `time.time() < file_epoch`: `await asyncio.sleep(file_epoch - time.time())`.
  - Nếu `time.time() >= file_epoch`: Có thể xoá file bằng `os.remove` để dọn dẹp.

### 3.3. Xử lý Fallback Models (extra_body)
- OpenAI SDK cho phép truyền dictionary thông qua tham số `extra_body`.
- Chỉnh sửa `call_kwargs`:
  ```python
  if self.fallback_models:
      call_kwargs["extra_body"] = {"models": self.fallback_models}
  ```
- Việc truyền thêm `model=fallback_models[0]` là bắt buộc để SDK không báo lỗi validation.

## 4. Kết luận
- Phương án gọi API `/auth/key` hoàn toàn khả thi bằng thư viện `httpx`.
- Cơ chế lưu thời gian vào file giúp đồng bộ đa tiến trình thành công, giải quyết triệt để lỗi 429 và hiện tượng spam (N+1).
