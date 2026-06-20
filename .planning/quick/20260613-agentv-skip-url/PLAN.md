---
slug: agentv-skip-url
date: 2026-06-13
---

# Quick Task: Add skip_url_keyword to AgentV

## Goal
Modify `AgentV` to optionally skip processing a challenge if the URL contains a specific keyword.

## Plan
1. Research how `AgentV` processes URLs in `_task_handler`.
2. Update `AgentV.__init__` in `src/hcaptcha_challenger/agent/challenger.py` to accept `skip_url_keyword: str | None = None`.
3. Update `_task_handler` to check if `self.skip_url_keyword` is in `response.url`. If so, skip the rest of the method execution.
