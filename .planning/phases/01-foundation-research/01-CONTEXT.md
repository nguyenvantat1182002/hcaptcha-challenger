# Phase 1: Foundation & Research - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Giai đoạn này tập trung vào việc nghiên cứu thư viện `humancursor`, thiết lập một adapter cho `DrissionPage` và xây dựng một prototype (script trực quan hóa) để so sánh quỹ đạo chuột cũ và mới.

</domain>

<decisions>
## Implementation Decisions

### Chiến lược tích hợp (Integration Strategy)
- **D-01:** Sử dụng logic tính toán quỹ đạo (như `BezierCalculator`) từ thư viện `humancursor` thay vì sử dụng trực tiếp các class `WebCursor`.
- **D-02:** Việc di chuyển chuột thực tế sẽ do `DrissionPageMouse` (trong `robotic.py`) đảm nhận để đảm bảo khả năng tương thích với `DrissionPage`.

### Quản lý Timing và Tốc độ
- **D-03:** Trích xuất các điểm tọa độ từ `humancursor` nhưng tự quản lý vòng lặp di chuyển và độ trễ (`sleep`).
- **D-04:** Tiếp tục hỗ trợ và tích hợp hệ số `AgentConfig.MOUSE_SPEED` vào vòng lặp di chuyển mới để người dùng có thể điều chỉnh tốc độ.

### Cấu trúc mã nguồn (Codebase Structure)
- **D-05:** Thực hiện refactor lại toàn bộ API của `src/hcaptcha_challenger/agent/mouse.py` để phản ánh đúng cấu trúc và logic của `humancursor`.
- **D-06:** Cập nhật `src/hcaptcha_challenger/agent/robotic.py` để tương thích với API mới của `mouse.py`.

### Mục tiêu Prototype
- **D-07:** Prototype cho Giai đoạn 1 sẽ là một script sử dụng `matplotlib` để vẽ và so sánh quỹ đạo chuột được tạo ra bởi thuật toán cũ so với thuật toán mới từ `humancursor`.

### Claude's Discretion
- Claude có thể quyết định cách tối ưu nhất để trích xuất logic toán học từ `humancursor` mà không làm tăng độ phức tạp của các dependencies.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Documentation
- `.planning/PROJECT.md` — Project context and high-level goals.
- `.planning/REQUIREMENTS.md` — Functional and non-functional requirements for HumanCursor integration.
- `.planning/ROADMAP.md` — Phase breakdown and progress tracking.

### Codebase Maps
- `.planning/codebase/ARCHITECTURE.md` — Overview of the agent and robotic layers.
- `.planning/codebase/STACK.md` — Current tech stack and dependencies (including `humancursor`).

### External Resources
- `https://github.com/riflosnake/HumanCursor` — Official repository and documentation for the target library.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/hcaptcha_challenger/agent/mouse.py`: Chứa các function signature (`human_move`, `human_click`) cần được giữ lại hoặc refactor.
- `src/hcaptcha_challenger/agent/robotic.py`: Class `DrissionPageMouse` là điểm kết nối chính để thực hiện di chuyển chuột trên trình duyệt.

### Established Patterns
- **Protocol-based Mouse:** `RawMouse` protocol được sử dụng để trừu tượng hóa các thao tác chuột cấp thấp.
- **Config-driven delays:** Sử dụng `AgentConfig` và các helper như `sleep_ms` để kiểm soát thời gian.

### Integration Points
- `src/hcaptcha_challenger/agent/mouse.py`: Nơi triển khai logic tạo quỹ đạo.
- `src/hcaptcha_challenger/agent/robotic.py`: Nơi gọi các hàm di chuyển chuột trong quá trình giải CAPTCHA.

</code_context>

<specifics>
## Specific Ideas
- Việc so sánh quỹ đạo qua đồ thị `matplotlib` sẽ giúp đánh giá trực quan độ "tự nhiên" và các đặc điểm như overshoot, jitter của thư viện mới.

</specifics>

<deferred>
## Deferred Ideas
- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Foundation & Research*
*Context gathered: 2026-05-01*
