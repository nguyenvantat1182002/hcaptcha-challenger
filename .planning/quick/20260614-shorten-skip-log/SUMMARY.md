---
status: complete
---

# Summary

Updated the logging logic in `_task_handler` when a challenge is skipped due to a `skip_url_keywords` match.
Previously, the code would print the entire `response.url` (which could be extremely long). It now formats and prints the precise rule that triggered the skip (e.g. `POST /api/v1/login` or just the string keyword), providing a concise and much cleaner log output.
