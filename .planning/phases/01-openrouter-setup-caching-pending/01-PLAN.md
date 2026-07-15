# Plan: Phase 1 (OpenRouter Setup & Caching)

## Goal
Tích hợp header `provider-sticky-routing` cho OpenRouter client để hỗ trợ Prompt Caching một cách tự động.

## Context & Constraints
- **Locked Decision**: Hardcode `provider-sticky-routing=true` cho mọi request.
- **File target**: `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`

## Implementation Steps

### Task 1: Update `OpenRouterProvider` Initialization
**File:** `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`
- Tìm hàm `__init__` của class `OpenRouterProvider`.
- Sửa tham số truyền vào khi khởi tạo `self.client = AsyncOpenAI(...)`.
- Bổ sung tham số `default_headers={"provider-sticky-routing": "true"}` bên cạnh `api_key`, `base_url`, và `timeout`.

### Task 2: Verify Import & Syntax
- Đảm bảo không thay đổi các logic của hàm `generate_with_images`, vì SDK sẽ tự động đính kèm `default_headers` vào mọi payload gửi đi.

## Verification
- Chạy type checking (ví dụ: `mypy`) hoặc linter (nếu dự án có) để chắc chắn cú pháp hợp lệ.
- Review lại code trực quan đảm bảo đúng như kế hoạch.
