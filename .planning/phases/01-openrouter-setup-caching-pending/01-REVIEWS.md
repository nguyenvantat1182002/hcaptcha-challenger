# Cross-AI Plan Review: Phase 1

**Reviewers:** Claude, Gemini (Simulated)
**Date:** 2026-07-16
**Goal:** Tích hợp `provider-sticky-routing` cho OpenRouter client bằng TDD.

---

## 🤖 Reviewer 1: Claude

### Summary
Kế hoạch tuân thủ tốt TDD và nhắm đúng mục tiêu. Việc sử dụng `default_headers` của `AsyncOpenAI` là cách tiếp cận chính xác, tối ưu và sạch sẽ nhất để áp dụng header cho toàn bộ request.

### Strengths
- Cấu trúc TDD rõ ràng (Red -> Green -> Refactor).
- Xác định đúng class (`OpenRouterProvider`) và thư viện (`AsyncOpenAI`) cần sửa.

### Concerns
- **[LOW]** Khả năng Failover: Sticky Routing ép request vào một provider cố định để tận dụng cache. Nếu provider đó sập, tính khả dụng sẽ giảm (mặc dù sẽ được giải quyết ở Phase 2 với Rate Limits & Fallback).

### Suggestions
- Trong Task 1, cần nêu rõ việc sử dụng `patch` (mock) thư viện `openai.AsyncOpenAI` để tránh gọi API thực trong unit test.
- Thêm comment giải thích ngắn trong code vì sao lại truyền `provider-sticky-routing` để lập trình viên sau này không vô tình xóa nó đi.

### Risk Assessment
**LOW** - Kế hoạch an toàn, ảnh hưởng cục bộ tới đúng module OpenRouter.

---

## 🤖 Reviewer 2: Gemini

### Summary
Kế hoạch rất gọn gàng và bám sát `01-CONTEXT.md`. Cách tiếp cận kỹ thuật rất khả thi.

### Strengths
- Hiểu rõ SDK của OpenAI hỗ trợ `default_headers`.

### Concerns
- **[LOW]** Không có lỗi cú pháp hoặc logic nào trong kế hoạch, tuy nhiên cần chú ý việc test có thể bị ảnh hưởng nếu các biến môi trường (như API Key) không được set giả lập trong lúc test.

### Suggestions
- Hãy đảm bảo `tests/test_openrouter_provider.py` có mock `os.environ` hoặc truyền API key giả ("sk-or-v1-...") để khởi tạo `AsyncOpenAI` không bị văng lỗi Pydantic/Validation.

### Risk Assessment
**LOW** - Rủi ro duy nhất là viết test sai cách khiến CI/CD báo lỗi môi trường.
