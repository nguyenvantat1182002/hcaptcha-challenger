# Cross-AI Reviews for Phase 2 (Post-Update)

## Reviewer: Antigravity (Self-Review / Logic Audit)

**Summary**
Bản kế hoạch mới đã tích hợp yêu cầu sử dụng API `/api/v1/auth/key` và cơ chế IPC File (`.openrouter_ratelimit`) để đồng bộ trạng thái đa tiến trình. Đây là thiết kế rất tốt cho môi trường nhiều agent. Tuy nhiên, logic hiện tại trong PLAN đang có một lỗ hổng nghiêm trọng (Critical Flaw) mâu thuẫn trực tiếp với mục tiêu "ngăn chặn 429 ở ngưỡng 70%".

**Strengths**
- [x] Cơ chế IPC File hoạt động hoàn hảo để chia sẻ State giữa các quá trình. 
- [x] Có chiến lược rõ ràng cho trường hợp `limit=null`.

**Concerns**
- **[CRITICAL] Mâu thuẫn logic "Tránh 429" và "Block except":** Mục tiêu yêu cầu là "khi sử dụng tới ngưỡng 70% thì sẽ sleep. Tránh xảy ra 429". Tuy nhiên, bước 2.1 của `02-PLAN.md` lại ghi rằng: *"ta sẽ gọi trong block `except RateLimitError`"*. 
  - *Vấn đề:* Nếu bạn đã nằm trong block `except`, nghĩa là request của bạn đã gửi đi và bị OpenRouter từ chối với mã 429! Bạn **không thể** tránh lỗi 429 nếu chỉ kiểm tra sau khi nó đã xảy ra.
- **[HIGH] Làm sao lấy được ngưỡng 70% mà không bị N+1?** Để tính được 70%, hệ thống phải biết được số request đang dùng. Nếu không đọc từ Header, mà muốn dùng API, bạn buộc phải gọi API `GET /auth/key` **trước** khi gửi request sinh chữ. Việc gọi API trước mỗi request sẽ gây ra lỗi N+1 request và cực kỳ chậm.

**Suggestions & Recommendation**
Để thoả mãn cả 2 yêu cầu: "Tránh 429 (ngưỡng 70%)" và "Sử dụng API /auth/key thay vì Header", cách duy nhất là:
1. **Khởi tạo (Initialization Check)**: Gọi `GET /auth/key` 1 lần ngay khi khởi tạo class `OpenRouterProvider` để lấy `rate_limit` ban đầu.
2. **Local Counter**: Tạo biến in-memory `self._request_count` để tự đếm số request đã gửi (local tracking). 
3. **Tính ngưỡng 70% (Local)**: Nếu `_request_count >= rate_limit.requests * 0.7`, thì gọi tiếp `GET /auth/key` để fetch lại thời gian reset chính xác. Sau đó lưu vào IPC file `.openrouter_ratelimit` và sleep!
(Hoặc chấp nhận gọi API định kỳ sau mỗi N request).

**Risk Assessment**
**CRITICAL.** Cần sửa lại bước thực hiện trong PLAN trước khi code. Bạn không thể "tránh 429" nếu đợi bắt lỗi 429 rồi mới kiểm tra!
