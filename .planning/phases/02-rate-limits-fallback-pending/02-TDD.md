# TDD & Verification: Phase 2 - Rate Limits & Fallback (API Based)

## 1. Mục tiêu (Verification Goal)
Đảm bảo cơ chế Rate Limit sử dụng API `/auth/key`, tạo file `.openrouter_ratelimit` hoạt động chính xác và cấu hình Fallback Models qua `extra_body` được truyền đi an toàn.

## 2. Test Cases (TDD)

### 2.1. Fallback Models Configuration
- **Given**: Biến môi trường `OPENROUTER_FALLBACK_MODELS="google/gemini-pro, anthropic/claude-3-opus"`.
- **When**: Khởi tạo `OpenRouterProvider` và gọi `generate_with_images()`.
- **Then**:
  - Thuộc tính `self.model` phải là `"google/gemini-pro"`.
  - API request (nếu mock) nhận được tham số `extra_body={"models": ["google/gemini-pro", "anthropic/claude-3-opus"]}`.

### 2.2. IPC File Lock - Proactive Sleep (Đồng bộ đa tiến trình)
- **Given**: File `.openrouter_ratelimit` đang tồn tại và chứa epoch time là `time.time() + 2.5` (2.5 giây nữa mới reset).
- **When**: Một instance gọi hàm `generate_with_images()`.
- **Then**:
  - Hệ thống phải tự động gọi `await asyncio.sleep(t)` với `t` xấp xỉ 2.5.
  - API request chỉ được gửi đi *sau* khi sleep hoàn thành.
  - Nếu file chứa thời gian trong quá khứ (`< time.time()`), hệ thống KHÔNG sleep và file sẽ bị xoá (hoặc bỏ qua).

### 2.3. Pre-flight Check & 70% Threshold
- **Given**: Biến `self._rate_limit_requests = 10` (mock từ API `__init__`), và `self._local_request_count = 6`. Mock thư viện `httpx.AsyncClient.get` trả về `rate_limit.interval = "10s"`.
- **When**: Gọi hàm `generate_with_images()` lần thứ 7 (vừa chạm ngưỡng `7 >= 10 * 0.7 = 7`).
- **Then**:
  - API `/auth/key` phải được gọi 1 lần bằng `httpx`.
  - File `.openrouter_ratelimit` **phải được tạo ra**.
  - Nội dung file chứa một số float `time.time() + reset_time` tính toán từ API.
  - Sau đó hàm chủ động `await asyncio.sleep(...)` trước khi cho phép gọi model thực sự.
  - `self._local_request_count` được reset về 0.

## 3. Test Strategy
- Sử dụng `pytest` và `pytest-asyncio`.
- Dùng `unittest.mock.patch` để mock:
  - `os.environ`
  - `httpx.AsyncClient.get` (để mock API `/auth/key` lúc init và lúc 70%)
  - `AsyncOpenAI.chat.completions.create` 
  - `asyncio.sleep` (để test chạy nhanh).
  - Thao tác IO (đọc/ghi `.openrouter_ratelimit`).
