# Phase 3: Thêm API cho solve. Kiểu API createTask xong có API getResult - Plan

**Status:** Ready for execution
**Phase:** 3
**Mode:** reviews

## 1. Goal
Xây dựng cơ chế gọi API bất đồng bộ (Async API) với luồng 2 bước: tạo task (`createTask`) và lấy kết quả (`getTaskResult`), giúp client không bị timeout.

## 2. Approach
Sử dụng một background thread chạy một Event Loop riêng rẽ (`asyncio.new_event_loop()`) trong Flask app. Các yêu cầu solve sẽ được gán một `taskId` (UUID) và được đẩy vào Event Loop ngầm thông qua `asyncio.run_coroutine_threadsafe()`. Trạng thái của task được lưu trữ tại một biến dictionary `pending_tasks` trên memory, và có cơ chế lazy cleanup dựa trên timeout.

**Lưu ý Triển khai (Deployment Constraint):** Kiến trúc In-memory Storage này chỉ hoạt động với **Single-process deployment** (VD: `gunicorn -w 1 --threads 4` hoặc chạy trực tiếp bằng `python`). Nếu chạy nhiều tiến trình worker, dữ liệu task sẽ bị rời rạc giữa các worker, gây lỗi 404 khi query kết quả. Điều này đã được thống nhất là chấp nhận được cho Phase này.

## 3. Tasks

### 1. Setup Background Event Loop & Task Storage (Thread-safe)
**File:** `src/hcaptcha_challenger/server/app.py`
- Khởi tạo biến global `pending_tasks = {}`.
- Khởi tạo `task_lock = threading.Lock()` để đảm bảo thread-safety khi đọc/ghi `pending_tasks`.
- Tạo biến `background_loop = None` và hàm `init_background_loop()` đảm bảo thread chỉ được khởi tạo 1 lần duy nhất, tránh tình trạng Flask reloader chạy file 2 lần sinh 2 threads.
- Thêm hàm helper `cleanup_expired_tasks()`: dùng `with task_lock:` trước khi lặp qua `list(pending_tasks.keys())` và xóa các task vượt quá `timeout`. (Lưu ý phải convert keys sang list để tránh lỗi RuntimeError).

### 2. Implement `/createTask` endpoint
**File:** `src/hcaptcha_challenger/server/app.py`
- Lấy `prompt`, `image`, `challenge_type`, `timeout` (mặc định 300s).
- Gọi `cleanup_expired_tasks()`.
- Tạo `task_id` bằng chuỗi UUID4.
- Sử dụng `with task_lock:` để lưu trạng thái ban đầu: `pending_tasks[task_id] = {"status": "processing", "result": None, "created_at": time.time(), "timeout": timeout}`.
- Định nghĩa coroutine wrapper để khởi tạo `SolverService`, gọi `solve_challenge`, và cập nhật kết quả. Sử dụng `with task_lock:` khi cập nhật lại `status` thành `"ready"` hoặc `"failed"` vào `pending_tasks`.
- Gọi `asyncio.run_coroutine_threadsafe(coroutine, background_loop)`.
- Trả về JSON: `{"success": True, "taskId": task_id}`.

### 3. Implement `/getTaskResult` endpoint
**File:** `src/hcaptcha_challenger/server/app.py`
- Lấy `taskId` từ request JSON.
- Gọi `cleanup_expired_tasks()`.
- Sử dụng `with task_lock:` để lấy thông tin task từ `pending_tasks`. Nếu không có, trả lỗi 404 (Task not found / expired).
- Dựa vào `status` của task:
  - `"processing"`: Trả về trạng thái đang xử lý.
  - `"ready"`: Trả về trạng thái ready cùng `solution: {"coordinates": result}`. Xóa task khỏi bộ nhớ (vẫn trong block `with task_lock:`).
  - `"failed"`: Trả về lỗi tương ứng. Xóa task khỏi bộ nhớ.

### 4. Remove Legacy `/solve` API
**File:** `src/hcaptcha_challenger/server/app.py`
- Xóa toàn bộ hàm `solve()` và route `@app.route("/solve", methods=["POST"])`.
- Không cần xóa `import asyncio` vì phần Async API đã sử dụng.

### 5. Update Documentation
**File:** `AGENT_SKILL.md`
- Thay thế tài liệu cho `/solve` bằng hướng dẫn gọi 2 bước `/createTask` và liên tục poll `/getTaskResult`.
- Cập nhật các đoạn code mẫu (Python và Node.js) để phản ánh logic gọi API mới.

### 6. Update Test Scripts
**File:** `test_solve.py`
- Sửa lại test script để gọi `/createTask` thay vì `/solve`, sau đó dùng vòng lặp `while` gọi `/getTaskResult` với `time.sleep(1)` để chờ kết quả.

## 4. Verification
- Chạy Flask server cục bộ (`python -m hcaptcha_challenger.server.app`).
- Dùng `curl` hoặc Postman gửi request `/createTask`.
- Lấy `taskId` gọi liên tục `/getTaskResult` cho đến khi chuyển sang `ready`.
- Test thử request chờ quá 5 phút để đảm bảo task bị dọn dẹp.
- Giả lập gọi đồng thời nhiều request để đảm bảo lock hoạt động không gây ra lỗi dictionary size changed during iteration.
