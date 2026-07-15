# Code Review: Phase 2 - Rate Limits & Fallback

## 1. Scope
- Reviewing `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`.
- **Reviewer**: Antigravity Code Reviewer
- **Depth**: Standard

## 2. Findings

### 2.1. [FIXED] Residual Header Parsing Logic
- **Severity**: Low (but violates design constraints).
- **Description**: Trong khối `except RateLimitError`, hệ thống vẫn còn sót lại đoạn code cũ thực hiện việc đọc header `x-ratelimit-reset` để tính thời gian. Điều này vi phạm nguyên tắc "chỉ sử dụng API làm source of truth" đã chốt trong `02-CONTEXT.md`.
- **Resolution**: **Đã được sửa chữa ngay lập tức (Auto-fixed)**. Đoạn code đọc header đã bị xóa hoàn toàn. Thay vào đó, nếu vô tình rơi vào `except RateLimitError` (ví dụ do burst traffic từ nhiều tiến trình cùng lúc), hệ thống sẽ chủ động gọi hàm `await self._fetch_rate_limits_async_and_lock()` để lấy thông tin từ API và ghi khóa vào file.

### 2.2. IPC File Lock Implementation
- **Severity**: Info.
- **Description**: Cơ chế đọc ghi file `Path(".openrouter_ratelimit")` hoạt động tốt. 
- **Observation**: File không gây side-effect nghiêm trọng, tự động xóa (unlink) khi hết hạn.

### 2.3. [REFACTORED] DRY (Don't Repeat Yourself) / Code Reuse
- **Severity**: Medium.
- **Description**: Đoạn code thiết lập `httpx.Client` gọi API `/auth/key` bị lặp lại ở cả bản đồng bộ (sync) lúc `__init__` và bản bất đồng bộ (async) lúc cập nhật File Lock. Việc gọi I/O chặn ngang ở hàm `__init__` cũng là một anti-pattern.
- **Resolution**: **Đã được tối ưu hoá (Auto-fixed)**. 
  - Đã xoá toàn bộ hàm `_fetch_rate_limits_sync` và loại bỏ lệnh gọi ở `__init__`.
  - Hợp nhất thành một hàm duy nhất `_fetch_api_rate_limits(update_lock: bool = False)`.
  - Áp dụng **Lazy Initialization**: Ở lần gọi `generate_with_images` đầu tiên, hệ thống sẽ sử dụng chính hàm async này để nạp thông số `self._rate_limit_requests`. Sau đó cũng dùng chính hàm này nếu cần lấy thời gian để lock IPC file.

## 3. Conclusion
Mã nguồn cho Phase 2 đã đạt chuẩn và tuân thủ tuyệt đối quy tắc loại bỏ 100% Header Parsing, đồng thời code đã được Refactor tối ưu để tái sử dụng tối đa. Code pass toàn bộ các bài kiểm thử tự động.
