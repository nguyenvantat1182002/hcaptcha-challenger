---
status: complete
---

# Summary

Updated the `skip_url_keywords` typing and logic to support HTTP method filtering. You can now pass a mix of strings, tuples, or dictionaries.
Examples:
- `['/login-token']` (Matches any method containing `/login-token`)
- `[('POST', '/api/v1/login')]` (Matches only POST requests containing `/api/v1/login`)
- `[{"method": "GET", "url": "/checkcaptcha/"}]` (Matches only GET requests with `/checkcaptcha/`)
