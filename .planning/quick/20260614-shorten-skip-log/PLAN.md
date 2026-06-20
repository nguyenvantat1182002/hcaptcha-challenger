---
slug: shorten-skip-log
date: 2026-06-14
---

# Quick Task: Shorten Skip URL Keyword Log

## Goal
Make the log output for URL skipping more concise by displaying only the matched rule instead of the full response URL, which can be overly long.

## Plan
1. In `_task_handler`, capture the actual `rule` that matched the URL.
2. Store this in `matched_rule` instead of just using a boolean flag `skip_match`.
3. Update the `logger.debug` call to output the `matched_rule` instead of `response.url`.
