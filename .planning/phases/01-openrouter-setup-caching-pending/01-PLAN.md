# Plan: Phase 1 (OpenRouter Setup & Caching)

## Goal
Tích hợp header `provider-sticky-routing` cho OpenRouter client để hỗ trợ Prompt Caching một cách tự động, sử dụng phương pháp Test-Driven Development (TDD).

## Context & Constraints
- **Locked Decision**: Hardcode `provider-sticky-routing=true` cho mọi request.
- **File target**: `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
- **Test target**: `tests/test_openrouter_provider.py`

## Implementation Steps

### Task 1: Write Failing Test [type: tdd]
**File:** `tests/test_openrouter_provider.py`
- Khởi tạo file test mới cho OpenRouter Provider (nếu chưa có).
- Viết test case `test_openrouter_provider_sticky_routing_header_injected`.
- Mở mock hoặc kiểm tra trực tiếp đối tượng `AsyncOpenAI` được tạo ra trong `OpenRouterProvider` để assert rằng cấu hình `default_headers` chứa key `"provider-sticky-routing": "true"`.
- Chạy test và đảm bảo test này **FAILED** (do code hiện tại chưa có header này).

### Task 2: Implement Code to Pass Test [type: tdd]
**File:** `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
- Tìm hàm `__init__` của class `OpenRouterProvider`.
- Sửa tham số truyền vào khi khởi tạo `self.client = AsyncOpenAI(...)`.
- Bổ sung tham số `default_headers={"provider-sticky-routing": "true"}`.
- Chạy lại test và đảm bảo test này **PASSED**.

### Task 3: Refactor & Verify
- Kiểm tra linter và type checking.
- Đảm bảo logic gọi LLM (`generate_with_images`) không bị lỗi khi đính kèm custom headers.
- Chạy toàn bộ test suite (`pytest`) để đảm bảo không phá vỡ logic cũ.

## Verification
- Lệnh chạy test: `pytest tests/test_openrouter_provider.py -v`
- Vòng đời TDD: Red -> Green -> Refactor.
