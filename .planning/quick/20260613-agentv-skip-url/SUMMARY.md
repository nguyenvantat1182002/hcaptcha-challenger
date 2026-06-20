---
status: complete
---

# Summary

Updated `skip_url_keywords` to be a `List[str]`. 
When `_task_handler` detects a matching keyword in `response.url`, it immediately notifies `_solve_captcha` by adding `None` to the payload queue and setting a `_skip_notified` flag.
`_review_challenge_type` reads this flag and returns the `"SKIP"` signal.
`_solve_captcha` immediately aborts execution when it receives `"SKIP"`, and `wait_for_challenge` successfully unblocks with a simulated passed state.
