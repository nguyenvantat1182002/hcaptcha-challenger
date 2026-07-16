# Phase 3: Thêm API cho solve. Kiểu API createTask xong có API getResult - Plan

**Status:** Ready for execution
**Phase:** 3
**Mode:** standard

## 1. Goal
Xây dựng cơ chế gọi API bất đồng bộ (Async API) với luồng 2 bước: tạo task (`createTask`) và lấy kết quả (`getTaskResult`), giúp client không bị timeout.

## 2. Approach
Sử dụng một background thread chạy một Event Loop riêng rẽ (`asyncio.new_event_loop()`) trong Flask app. Các yêu cầu solve sẽ được gán một `taskId` (UUID) và được đẩy vào Event Loop ngầm thông qua `asyncio.run_coroutine_threadsafe()`. Trạng thái của task được lưu trữ tại một biến dictionary `pending_tasks` trên memory, và có cơ chế lazy cleanup dựa trên timeout.

## 3. Tasks

### 1. Setup Background Event Loop & Task Storage
**File:** `src/hcaptcha_challenger/server/app.py`
- Khởi tạo biến global `pending_tasks = {}`.
- Tạo một background thread chạy `loop.run_forever()` (daemon thread).
- Thêm hàm helper `cleanup_expired_tasks()` quét qua `pending_tasks` và xóa các task vượt quá `timeout`.

### 2. Implement `/createTask` endpoint
**File:** `src/hcaptcha_challenger/server/app.py`
- Lấy `prompt`, `image`, `challenge_type`, `timeout` (mặc định 300s).
- Gọi `cleanup_expired_tasks()`.
- Tạo `task_id` bằng UUID4. 
- Lưu trạng thái ban đầu: `{"status": "processing", "result": None, "created_at": time.time(), "timeout": timeout}`.
- Định nghĩa coroutine wrapper để khởi tạo `SolverService`, gọi `solve_challenge`, và cập nhật kết quả/báo lỗi vào `pending_tasks[task_id]`.
- Gọi `asyncio.run_coroutine_threadsafe(coroutine, background_loop)`.
- Trả về JSON: `{"success": True, "taskId": task_id}`.

### 3. Implement `/getTaskResult` endpoint
**File:** `src/hcaptcha_challenger/server/app.py`
- Lấy `taskId` từ request JSON.
- Gọi `cleanup_expired_tasks()`.
- Kiểm tra `taskId` trong `pending_tasks`. Nếu không có, trả lỗi 404 (Task not found / expired).
- Dựa vào `status` của task:
  - `"processing"`: Trả về trạng thái đang xử lý.
  - `"ready"`: Trả về trạng thái ready cùng `solution: {"coordinates": result}`. Xóa task khỏi bộ nhớ.
  - `"failed"`: Trả về lỗi tương ứng. Xóa task khỏi bộ nhớ.

## 4. Verification
- Chạy Flask server cục bộ (`python -m hcaptcha_challenger.server.app` hoặc script tương ứng).
- Dùng `curl` hoặc Postman gửi request `/createTask`.
- Lấy `taskId` gọi liên tục `/getTaskResult` cho đến khi chuyển sang `ready`.
- Test thử request chờ quá 5 phút để đảm bảo task bị dọn dẹp.
