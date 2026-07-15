# Research: Phase 1 (OpenRouter Setup & Caching)

## 1. Goal Overview
Thêm cấu hình Prompt Caching (thông qua Sticky Routing) vào client gọi API của OpenRouter trong `hcaptcha-challenger`.

## 2. Technical Approach
- **OpenRouter Caching Mechanism**: OpenRouter hỗ trợ Prompt Caching cho các model của Anthropic, OpenAI, Google v.v. Để tối ưu hóa tỷ lệ "cache hit", tài liệu OpenRouter (được lưu trong LLM Wiki) khuyến nghị sử dụng HTTP header `provider-sticky-routing: true`. Việc này giúp OpenRouter điều hướng các request liên tiếp tới cùng một instance của nhà cung cấp.
- **Python Integration**: `OpenRouterProvider` trong hệ thống hiện tại đang sử dụng thư viện `openai.AsyncOpenAI`. Thư viện này hỗ trợ truyền các HTTP headers bổ sung (bao gồm custom headers) vào constructor thông qua tham số `default_headers`.

## 3. Findings & Trade-offs
| Approach | Pros | Cons |
|----------|------|------|
| **Truyền `default_headers` vào `AsyncOpenAI` client** | Áp dụng cho mọi request, code sạch sẽ, không cần sửa đổi nhiều hàm gọi API. | Toàn bộ các request đều dùng chung (phù hợp với Context của Phase này do user đã quyết định hardcode). |
| Truyền `extra_headers` vào từng hàm `create()` | Linh hoạt trên từng request. | Lặp code, rườm rà. |

## 4. Validation Architecture
- Kiểm tra tính hợp lệ của cú pháp khởi tạo `AsyncOpenAI(..., default_headers={"provider-sticky-routing": "true"})`.
- Đảm bảo các parameters hiện tại như `base_url` và `api_key` không bị ảnh hưởng.
