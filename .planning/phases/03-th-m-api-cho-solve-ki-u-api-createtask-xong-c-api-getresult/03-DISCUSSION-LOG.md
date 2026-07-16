# Phase 3: Thêm API cho solve. Kiểu API createTask xong có API getResult - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-16
**Phase:** 03-th-m-api-cho-solve-ki-u-api-createtask-xong-c-api-getresult
**Areas discussed:** Task Storage, Background Execution, Cleanup & TTL

---

## Quản lý trạng thái Task (Task Storage)

| Option | Description | Selected |
|--------|-------------|----------|
| In-memory dict | Sử dụng dict in-memory để lưu trạng thái | ✓ |
| Database/Redis | Tích hợp CSDL hoặc Redis | |

**User's choice:** 1. Dùng bộ nhớ tạm (in-memory)
**Notes:** Giữ kiến trúc đơn giản cho Flask app.

---

## Thực thi ngầm (Background Execution)

| Option | Description | Selected |
|--------|-------------|----------|
| Flask Async / asyncio | Dùng async nội tại hoặc event loop ngầm trong process | ✓ |
| Celery / Worker | Sử dụng message broker và worker tách biệt | |

**User's choice:** 2. Flask có async mà
**Notes:** Flask 2.0+ hỗ trợ async routes. Cần kiểm tra kỹ về background task khi sử dụng Flask thuần async, hoặc chạy task trực tiếp bằng `asyncio.create_task`.

---

## Cơ chế dọn dẹp (Cleanup & TTL)

| Option | Description | Selected |
|--------|-------------|----------|
| Cố định 5-10 phút | Hardcode thời gian dọn dẹp task | |
| Tùy chỉnh (Configurable) | Người dùng tự setup timeout | ✓ |

**User's choice:** 3. Cho người dùng setup timeout
**Notes:** Cơ chế tự dọn dẹp sẽ phụ thuộc vào thông số timeout người dùng truyền vào (TTL động).

---

## the agent's Discretion

None.

## Deferred Ideas

None.
