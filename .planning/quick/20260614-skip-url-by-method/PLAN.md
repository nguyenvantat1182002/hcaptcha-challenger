---
slug: skip-url-by-method
date: 2026-06-14
---

# Quick Task: Match skip_url_keywords by HTTP Method

## Goal
Enhance the `skip_url_keywords` argument to allow detecting by HTTP method (`GET` or `POST`) in addition to URL path keywords.

## Plan
1. Update `__init__` signature in `AgentV` to accept a list containing strings, tuples, or dictionaries.
2. In `_task_handler`, iterate through the list:
    - `str`: Match URL keyword only.
    - `tuple`: Match `(method, keyword)`.
    - `dict`: Match `{"method": "POST", "url": "/login"}`.
