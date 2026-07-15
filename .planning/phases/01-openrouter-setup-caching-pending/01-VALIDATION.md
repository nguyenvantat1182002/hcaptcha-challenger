# Validation Strategy: Phase 1

## Dimension 1: Functional Requirements (OR-01, OR-02)
- [ ] Provider khởi tạo thành công với thư viện `AsyncOpenAI`.
- [ ] Thuộc tính `default_headers` của client chứa `provider-sticky-routing: true`.

## Dimension 2: Resiliency
- [ ] Việc thêm custom header không gây crash thư viện OpenAI SDK.

## Dimension 8: Architectural Adherence
- [ ] Bám sát quyết định từ `01-CONTEXT.md` (hardcode Sticky Routing, không thêm config phức tạp).
