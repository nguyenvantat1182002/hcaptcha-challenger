# Plan: Phase 1 (OpenRouter Setup & Caching)

## Goal
Tích hợp header `provider-sticky-routing` cho OpenRouter client để hỗ trợ Prompt Caching một cách tự động, sử dụng phương pháp Test-Driven Development (TDD).

*(Bản kế hoạch đã được tinh chỉnh lại dựa trên REVIEWS.md)*

## Context & Constraints
- **Locked Decision**: Hardcode `provider-sticky-routing=true` cho mọi request.
- **File target**: `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
- **Test target**: `tests/test_openrouter_provider.py`

## Implementation Steps

### Task 1: Write Failing Test [type: tdd]
**File:** `tests/test_openrouter_provider.py`
- Khởi tạo file test mới cho OpenRouter Provider (nếu chưa có).
- Viết test case `test_openrouter_provider_sticky_routing_header_injected`.
- **(Review Requirement):** Cần truyền một `api_key` giả (ví dụ `"sk-or-v1-dummy"`) trong hàm khởi tạo hoặc mock `os.environ` để bypass quá trình xác thực validation của OpenAI SDK, tránh lỗi ngoại lệ không đáng có trong test.
- Mở mock hoặc kiểm tra trực tiếp đối tượng `AsyncOpenAI` được tạo ra trong `OpenRouterProvider` để assert rằng cấu hình `default_headers` chứa key `"provider-sticky-routing": "true"`.
- Chạy test và đảm bảo test này **FAILED** (do code hiện tại chưa có header này).

### Task 2: Implement Code to Pass Test [type: tdd]
**File:** `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
- Tìm hàm `__init__` của class `OpenRouterProvider`.
- Sửa tham số truyền vào khi khởi tạo `self.client = AsyncOpenAI(...)`.
- Bổ sung tham số `default_headers={"provider-sticky-routing": "true"}`.
- **(Review Requirement):** Thêm comment inline phía trên khai báo `default_headers` giải thích lý do: `# Bắt buộc thêm provider-sticky-routing để tận dụng Prompt Caching của OpenRouter.`
- Chạy lại test và đảm bảo test này **PASSED**.

### Task 3: Refactor & Verify
- Kiểm tra linter và type checking.
- Đảm bảo logic gọi LLM (`generate_with_images`) không bị lỗi khi đính kèm custom headers.
- Chạy toàn bộ test suite (`pytest`) để đảm bảo không phá vỡ logic cũ.

## Verification
- Lệnh chạy test: `pytest tests/test_openrouter_provider.py -v`
- Vòng đời TDD: Red -> Green -> Refactor.
