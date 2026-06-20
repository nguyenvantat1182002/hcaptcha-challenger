# Phase 2: Implement Solver Endpoint - Context
*Gathered: 2026-06-20*

<domain>
## Phase Boundary
Build the POST endpoint to receive images and prompts and return LLM solver coordinates.
</domain>

<decisions>
## Implementation Decisions

### Input Format
- Chỉ hỗ trợ `application/json` với payload chứa `prompt` và ảnh dưới dạng chuỗi base64. Quyết định này giúp dễ dàng tích hợp với client JS thuần.

### Solver Agent Lifecycle
- Khởi tạo Agent một lần (global/singleton) khi ứng dụng Flask khởi động. Điều này giúp tối ưu tốc độ xử lý request (latency thấp) dù tiêu tốn thêm một ít RAM để giữ model/context thường trực.

### Output Coordinate Format
- Danh sách object (List of dicts): `[{"x": 10, "y": 20}, {"x": 30, "y": 40}]`. Rõ ràng và dễ map sang các class/struct trên client.
</decisions>

<canonical_refs>
## Canonical References
- `ROADMAP.md` — Phase 2 definitions.
- `REQUIREMENTS.md` — Epic: hCaptcha Flask API Core Capabilities
</canonical_refs>

---

*Phase: 02-implement-solver-endpoint*
