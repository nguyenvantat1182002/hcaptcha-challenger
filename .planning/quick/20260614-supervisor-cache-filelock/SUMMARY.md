---
status: complete
---

# Summary

Added `FileLock` (from the `filelock` package) to `SupervisorCache` to safely handle file I/O operations.
The `_load` and `_save` cycle inside `get_guideline`, `save_guideline`, and `increment_fail_count` is now wrapped in a file-based lock with a timeout. This ensures that even if multiple workers or threads execute the challenge logic simultaneously, the `supervisor.json` cache will not face race conditions leading to overwritten or corrupted data.
