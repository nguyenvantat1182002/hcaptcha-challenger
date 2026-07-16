# Phase 3: Validation Strategy

## Overview
This document outlines the validation strategy for Phase 3 (Thêm API cho solve).

## Validation Architecture
- **In-Memory Dictionary Test**: Verify that tasks can be created and retrieved from the global dictionary.
- **Background Thread Test**: Submit a task to the background event loop, ensure `/createTask` returns immediately with a `taskId`.
- **TTL/Cleanup Test**: Verify that tasks older than the specified timeout are removed from the dictionary.
- **End-to-End Test**: Simulate a `/createTask` request followed by a `/getTaskResult` request, ensuring the result is available after processing completes.
