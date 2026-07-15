# Requirements

## v1 Requirements

### API Provider Integration
- [ ] **OR-01**: Hệ thống có khả năng gọi OpenRouter API như một provider cho các request LLM.
- [ ] **OR-02**: Request gửi lên OpenRouter chứa header `provider-sticky-routing=true` để tối ưu Prompt Caching.

### Resiliency (Độ bền bỉ)
- [ ] **RES-01**: Hệ thống áp dụng Exponential Backoff khi nhận mã lỗi HTTP 429 (Too Many Requests).
- [ ] **RES-02**: Hệ thống áp dụng cấu hình Fallback Routing (truyền mảng models thay vì một chuỗi duy nhất nếu được yêu cầu) khi gọi OpenRouter.

## v2 Requirements
- Hỗ trợ báo cáo chi phí dựa trên hiệu quả Prompt Caching.

## Out of Scope
- Tự động thay đổi provider thông qua code thủ công dựa trên giá cả theo thời gian thực (để tính năng Auto-router của OpenRouter lo việc này).

## Traceability
*To be filled by roadmap generator.*
