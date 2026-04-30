# AGENTS Guide

This repository uses GSD planning artifacts in `.planning/` as the source of truth for execution.

## Workflow

1. Read `.planning/PROJECT.md` for project context and constraints.
2. Read `.planning/REQUIREMENTS.md` for requirement scope and traceability.
3. Read `.planning/ROADMAP.md` for phase goals and success criteria.
4. Read `.planning/STATE.md` for current project status before starting work.

## Current Project Focus

- Project: `hcaptcha-challenger`
- Active objective: migrate cursor movement to HumanCursor-style behavior with compatibility-first rollout.
- Next command after initialization: `/gsd-plan-phase 1`

## Guardrails

- Preserve backward-compatible default behavior unless requirement explicitly changes it.
- Keep requirement-to-phase traceability updated when roadmap or scope changes.
- Validate changes against phase success criteria before phase completion.
