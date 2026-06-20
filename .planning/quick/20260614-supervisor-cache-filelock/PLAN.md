---
slug: supervisor-cache-filelock
date: 2026-06-14
---

# Quick Task: Fix SupervisorCache Race Condition

## Goal
Implement a locking mechanism in `SupervisorCache` to prevent Race Conditions when multiple processes attempt to read and write to the cache JSON file simultaneously.

## Plan
1. Import `FileLock` from the `filelock` package in `cache.py`.
2. Define a `.lock` file corresponding to the cache file path.
3. Wrap all atomic read-modify-write logic inside `get_guideline`, `save_guideline`, and `increment_fail_count` with `with FileLock(..., timeout=10)`.
