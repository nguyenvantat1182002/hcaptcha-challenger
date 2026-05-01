# Codebase Structure

**Analysis Date:** 2025-04-18

## Directory Layout

```
[project-root]/
├── src/hcaptcha_challenger/
│   ├── agent/          # Orchestration and human-like interaction logic
│   ├── cli/            # Command-line interface entry points
│   ├── helper/         # Visual aids, image processing, and utility scripts
│   ├── skills/         # Prompt engineering layer and template management
│   ├── tools/          # Specialized AI reasoners and LLM providers
│   ├── models.py       # Core Pydantic data models and enums
│   ├── utils.py        # General-purpose utility functions
│   └── __init__.py     # Package initialization
├── tests/              # Test suite (unit, integration, and functional)
├── examples/           # Usage demos for different scenarios (Playwright, DrissionPage)
├── docker/             # Containerization files (Dockerfile, compose)
├── docs/               # Documentation and research notebooks
└── pyproject.toml      # Project metadata and dependency configuration
```

## Directory Purposes

**`src/hcaptcha_challenger/agent/`:**
- Purpose: High-level orchestration and browser control.
- Contains: `AgentV` (orchestrator), `RoboticArm` (executor), and human-like mouse simulation.
- Key files: `challenger.py`, `robotic.py`, `mouse.py`.

**`src/hcaptcha_challenger/skills/`:**
- Purpose: Manages "Skills" - specialized prompts for different challenge types.
- Contains: `SkillManager`, YAML rules, and a library of markdown templates.
- Key files: `manager.py`, `library/*.md`.

**`src/hcaptcha_challenger/tools/`:**
- Purpose: Specialized AI reasoning engines.
- Contains: Logic for image classification, spatial path/point reasoning, and AI model providers.
- Key files: `image_classifier/`, `spatial/`, `challenge_router/`, `internal/providers/`.

**`src/hcaptcha_challenger/helper/`:**
- Purpose: Visual and image-processing helpers.
- Contains: Coordinate grid generators, screenshot visualizers, and format converters.
- Key files: `create_coordinate_grid.py`, `visualize_attention_points.py`, `webm_to_mp4.py`.

## Key File Locations

**Entry Points:**
- `src/hcaptcha_challenger/cli/main.py`: Main CLI entry point.
- `src/hcaptcha_challenger/agent/challenger.py`: Main library entry point (`AgentV`).

**Configuration:**
- `src/hcaptcha_challenger/agent/config.py`: Agent and global configuration settings.
- `pyproject.toml`: Dependency and build configuration.

**Core Logic:**
- `src/hcaptcha_challenger/agent/robotic.py`: Core challenge solving loop and tool integration.
- `src/hcaptcha_challenger/tools/internal/providers/`: Integration with LLM APIs (Gemini, OpenRouter).

**Testing:**
- `tests/`: Contains specific tests for tools, schemas, and helpers.

## Naming Conventions

**Files:**
- Snake case: `challenger.py`, `image_classifier.py`.

**Directories:**
- Snake case: `challenge_router`, `spatial`.

**Classes:**
- PascalCase: `AgentV`, `RoboticArm`, `SkillManager`.

## Where to Add New Code

**New Challenge Type Support:**
- Define schema in `src/hcaptcha_challenger/models.py`.
- Add a new tool in `src/hcaptcha_challenger/tools/`.
- Add prompt templates in `src/hcaptcha_challenger/skills/library/` and update `rules.yaml`.
- Integrate into `RoboticArm` in `src/hcaptcha_challenger/agent/robotic.py`.

**New AI Provider:**
- Implementation: `src/hcaptcha_challenger/tools/internal/providers/` (inheriting from `protocol.py`).

**New Utility:**
- Shared helpers: `src/hcaptcha_challenger/helper/`.

## Special Directories

**`src/hcaptcha_challenger/logs/`:**
- Purpose: Runtime, error, and serialization logs.
- Generated: Yes
- Committed: No

**`tmp/` (or configured cache dir):**
- Purpose: Caching screenshots, model answers, and downloaded skills.
- Generated: Yes
- Committed: No

---

*Structure analysis: 2025-04-18*
