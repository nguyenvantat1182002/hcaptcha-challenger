# -*- coding: utf-8 -*-
"""
YesCaptcha domain exceptions.
"""


class YesCaptchaError(Exception):
    """Base exception for all YesCaptcha errors."""


class YesCaptchaTaskError(YesCaptchaError):
    """Raised when the YesCaptcha API returns an error response or non-zero errorId."""

    def __init__(
        self,
        message: str,
        error_id: int | None = None,
        error_code: str | None = None,
        error_description: str | None = None,
    ):
        super().__init__(message)
        self.error_id = error_id
        self.error_code = error_code
        self.error_description = error_description


class YesCaptchaTimeoutError(YesCaptchaError):
    """Raised when polling a YesCaptcha task exceeds maximum attempts or timeout."""
