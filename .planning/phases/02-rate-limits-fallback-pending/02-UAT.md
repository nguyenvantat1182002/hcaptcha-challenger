# UAT: Phase 2 - Rate Limits & Fallback

## 1. UAT Scope & Criteria
Dựa vào `02-CONTEXT.md`, tính năng này được đánh giá hoàn thành nếu:
1. **Fallback Models Configuration**: Đọc và nạp đúng cấu hình `OPENROUTER_FALLBACK_MODELS`.
2. **Handling Rate Limits & 70% Threshold**:
   - Chỉ sử dụng API `/auth/key` làm Source of Truth (không đọc Header).
   - Có cơ chế Lazy Initialization.
   - Khi local count vượt 70% API limit, hệ thống sẽ parse `interval`, tính thời gian reset và chủ động `sleep`.
3. **IPC File Lock**:
   - Ghi thời gian sleep ra file `.openrouter_ratelimit`.
   - Các tiến trình (process) khác đều phải chờ đồng bộ (cross-process locking).

## 2. Test Execution & Results

| Test Case | Phương pháp (How) | Kết quả (Status) |
| :--- | :--- | :--- |
| **TC1: Unit Tests** | Chạy `pytest tests/test_openrouter_provider.py`. | **[Pass]** 1/1 passed. Code logic không có lỗi syntax hay runtime cơ bản. |
| **TC2: Proactive 70% Limit** | Chạy kịch bản `test_429_real.py` (Test 1). Ép `limit=3`. | **[Pass]** Tới request thứ 3, hệ thống đã dừng chặn và sleep 9.99s chính xác. Không hề có request vượt mức được gửi đi. |
| **TC3: Cross-process IPC Lock** | Chạy kịch bản `test_429_real.py` (Test 2) với 2 instance chạy song song. | **[Pass]** Cả hai instance cùng lúc đọc file `.openrouter_ratelimit` và ngủ đúng ~5.00s trước khi thực thi. Cơ chế Multi-process hoạt động trơn tru. |
| **TC4: No Header Parsing** | Thực hiện `/gsd-code-review` để kiểm tra tĩnh. | **[Pass]** Đã auto-fix thành công. Code hiện tại chỉ gọi API `await self._fetch_api_rate_limits(update_lock=True)` khi gặp lỗi, loại bỏ hoàn toàn việc đọc `x-ratelimit-reset`. |

## 3. Findings & Adjustments
- **Phát hiện**: Trong quá trình review tĩnh, phát hiện ra code ban đầu còn sót phần đọc header khi rớt vào block `except RateLimitError`. Đồng thời, logic gọi API `/auth/key` bị lặp lại ở hàm khởi tạo.
- **Khắc phục**: Đã xoá toàn bộ phần đọc header và hợp nhất code bằng cơ chế Lazy Initialization (`_fetch_api_rate_limits`). Fix đã được merge và pass kiểm thử hồi quy (Regression Test).

## 4. Conclusion
Tất cả các tiêu chí nghiệm thu (UAT) cho Phase 2 đã đạt 100%. Không tìm thấy lỗi (gap) nào.

Phase 2 đã **Hoàn Thành**.
