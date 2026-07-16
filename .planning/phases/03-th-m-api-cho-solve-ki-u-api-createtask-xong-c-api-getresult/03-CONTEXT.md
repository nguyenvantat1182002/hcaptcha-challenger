# Phase 3: Thêm API cho solve. Kiểu API createTask xong có API getResult - Context

**Gathered:** 2026-07-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Xây dựng cơ chế gọi API bất đồng bộ (Async API) với luồng 2 bước: tạo task (`createTask`) và lấy kết quả (`getTaskResult`), giúp client không bị timeout khi việc giải quyết hCaptcha mất nhiều thời gian.

</domain>

<decisions>
## Implementation Decisions

### Quản lý trạng thái Task (Task Storage)
- **D-01:** Sử dụng cấu trúc bộ nhớ tạm (in-memory dict) của Python để lưu trữ danh sách các task đang chờ và kết quả (sẽ mất dữ liệu khi restart nhưng chấp nhận được cho API solve).

### Thực thi ngầm (Background Execution)
- **D-02:** Tận dụng tính năng async nội tại của Flask. Khởi tạo coroutine bằng `asyncio.create_task` (hoặc Event Loop ngầm) trực tiếp trong Flask thay vì dùng Message Broker bên ngoài.

### Cơ chế dọn dẹp (Cleanup & TTL)
- **D-03:** Hỗ trợ tính năng thiết lập timeout do người dùng định nghĩa. Việc dọn dẹp bộ nhớ (cleanup) dựa trên timeout này.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture
- `.planning/codebase/ARCHITECTURE.md` — Agentic Workflow and Pluggable Resources logic
- `.planning/codebase/STRUCTURE.md` — Current API is located at `src/hcaptcha_challenger/server/`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/hcaptcha_challenger/server/app.py`: Route `/solve` hiện tại có thể tham khảo logic khởi tạo `SolverService` và truyền payload.
- `SolverService`: Hàm `solve_challenge` là async và trả về kết quả tọa độ.

### Integration Points
- Flask App Routes: Sẽ thêm các routes mới (VD: `/createTask`, `/getTaskResult`) trong `app.py`.

</code_context>

<specifics>
## Specific Ideas

Người dùng muốn tự do setup cấu hình timeout (có thể qua API payload hoặc biến môi trường).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 3-th-m-api-cho-solve-ki-u-api-createtask-xong-c-api-getresult*
*Context gathered: 2026-07-16*
