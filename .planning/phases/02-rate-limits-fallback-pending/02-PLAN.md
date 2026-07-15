# Plan: Phase 2 - Rate Limits & Fallback (API Based)

## 1. Mục tiêu (Goal)
Cập nhật `OpenRouterProvider` (`provider.py`) để truyền cấu hình Fallback qua thư viện `AsyncOpenAI`, đồng thời tích hợp cơ chế theo dõi Rate Limit bằng cách gọi trực tiếp API `/api/v1/auth/key`, thiết lập file lock để đồng bộ quá trình `sleep` đa tiến trình khi giới hạn chạm ngưỡng 70%.

## 2. Phạm vi thay đổi (Scope of Changes)
### 2.1. `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
- Import `os`, `asyncio`, `time`.
- Bổ sung logic xử lý Fallback Models:
  - Đọc biến môi trường `OPENROUTER_FALLBACK_MODELS`.
  - Đính kèm `extra_body={"models": fallback_models_list}` vào `call_kwargs` và thiết lập `model=fallback_models_list[0]`.
- Logic Proactive Sleep qua IPC File (`.openrouter_ratelimit`):
  - Khởi tạo biến theo dõi local `self._local_request_count = 0` và `self._rate_limit_requests = None`.
  - Trong `__init__` (hoặc lazy-load lần đầu), gọi API `GET /api/v1/auth/key` 1 lần để lấy thông số giới hạn (ví dụ: lấy từ `rate_limit.requests`).
  - Ở đầu hàm `generate_with_images`, kiểm tra file `.openrouter_ratelimit`. Nếu tồn tại file và chưa quá hạn, gọi `await asyncio.sleep(file_epoch - time.time())`.
  - Tăng `self._local_request_count += 1`.
  - **Kiểm tra ngưỡng 70%**: Nếu `self._rate_limit_requests` tồn tại và `self._local_request_count >= self._rate_limit_requests * 0.7`:
    - Chủ động gọi lại API `/auth/key` để tính toán chính xác thời gian reset.
    - Ghi thời gian reset (epoch time) ra file `.openrouter_ratelimit`.
    - Chủ động `sleep()` tương ứng. Reset `self._local_request_count = 0`.
  - Cơ chế này đảm bảo không gây lỗi N+1 request nhờ Local Counter, đồng thời chủ động ngăn chặn triệt để lỗi 429 theo đúng Review Feedback.

## 3. Các bước thực hiện (Execution Steps)
1. **[MODIFY]** `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
   - Bổ sung cấu hình `fallback_models` vào `__init__`.
   - Viết hàm `_fetch_rate_limits()` để gọi `GET /auth/key`.
   - Viết hàm `_check_ipc_lock_and_sleep(self)` được gọi đầu hàm `generate_with_images`.
   - Bổ sung logic tăng `_local_request_count` và kiểm tra ngưỡng 70% ngay trước khi gửi request tới model.
   - Bổ sung ghi IPC File lock và sleep nếu vượt ngưỡng.
   - Truyền `extra_body` vào `call_kwargs`.

## 4. Tiêu chí nghiệm thu (Acceptance Criteria)
- [ ] Tham số Fallback Models được truyền vào request API qua `extra_body`.
- [ ] API `GET /api/v1/auth/key` được sử dụng để lấy thông tin key.
- [ ] Trạng thái reset được lưu thành file `.openrouter_ratelimit` (IPC Lock).
- [ ] Đa tiến trình không gọi API chồng chéo khi một tiến trình đã tạo IPC Lock.
