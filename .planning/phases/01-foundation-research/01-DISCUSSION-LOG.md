# Phase 1: Foundation & Research - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 01-Foundation & Research
**Areas discussed:** Integration Strategy, Timing & Speed, Codebase Structure, Prototype Goal

---

## Integration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Lựa chọn A | Tạo một lớp "Shim" giả lập driver Selenium để sử dụng trực tiếp class `WebCursor`. | |
| Lựa chọn B | Chỉ sử dụng logic tính toán quỹ đạo từ `humancursor` và tự thực hiện việc di chuyển bằng `DrissionPage`. | ✓ |

**User's choice:** Lựa chọn B
**Notes:** Giữ nguyên adapter `DrissionPageMouse` hiện có để thực hiện các thao tác chuột thực tế.

---

## Timing & Speed

| Option | Description | Selected |
|--------|-------------|----------|
| Lựa chọn A | Để `humancursor` tự quản lý việc `sleep` (chặn thread khi di chuyển). | |
| Lựa chọn B | Lấy danh sách các điểm tọa độ nhưng tự quản lý vòng lặp di chuyển và độ trễ để hỗ trợ `MOUSE_SPEED`. | ✓ |

**User's choice:** Lựa chọn B
**Notes:** Cần duy trì khả năng điều chỉnh tốc độ chuột thông qua `AgentConfig.MOUSE_SPEED`.

---

## Codebase Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Lựa chọn A | Xóa code cũ nhưng giữ nguyên function signature để giảm thiểu thay đổi ở các file khác. | |
| Lựa chọn B | Refactor lại toàn bộ API của `mouse.py` để phản ánh đúng cấu trúc của `humancursor`. | ✓ |

**User's choice:** Lựa chọn B
**Notes:** Ưu tiên kiến trúc sạch và tuân thủ thư viện mới, chấp nhận việc cập nhật `robotic.py`.

---

## Prototype Goal

| Option | Description | Selected |
|--------|-------------|----------|
| Lựa chọn A | Một script vẽ biểu đồ (matplotlib) để so sánh quỹ đạo cũ và mới. | ✓ |
| Lựa chọn B | Một script chạy thực tế trên trình duyệt. | |

**User's choice:** Lựa chọn A
**Notes:** Sử dụng đồ thị để đánh giá độ tự nhiên của quỹ đạo chuột mới trước khi triển khai thực tế.

---

## Claude's Discretion
- Cách thức trích xuất logic toán học tối ưu từ mã nguồn `humancursor`.

## Deferred Ideas
- None.
