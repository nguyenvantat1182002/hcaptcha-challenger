# Codebase Structure

**Analysis Date:** 2025-05-15

## Directory Layout

```
hcaptcha-challenger/
├── .github/                # GitHub Actions workflows and templates
├── docker/                 # Docker configuration (Dockerfile, compose)
├── docs/                   # Documentation and research notebooks (Jupyter)
├── examples/               # Usage examples and demo scripts
├── src/
│   └── hcaptcha_challenger/ # Primary source code
│       ├── agent/          # Core agent orchestration logic
│       ├── cli/            # Command-line interface subcommands
│       ├── helper/         # UI/Visual helpers and internal utilities
│       ├── logs/           # Runtime log files (organized by date)
│       ├── skills/         # Prompt templates and matching rules
│       ├── tools/          # Reasoning engines (LLM wrappers)
│       ├── models.py       # Shared data models (Pydantic)
│       ├── utils.py        # Generic utility functions
│       └── __init__.py     # Package entry point
├── tests/                  # Test suites and mock artifacts
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # Project documentation
```

## Directory Purposes

**src/hcaptcha_challenger/agent/:**
- Purpose: Orchestrates the high-level flow of solving a captcha.
- Contains: Interaction logic, mouse simulation, and agent configuration.
- Key files: `challenger.py`, `robotic.py`, `config.py`, `mouse.py`.

**src/hcaptcha_challenger/tools/:**
- Purpose: Implements the "intelligence" of the system.
- Contains: Specific reasoners for different challenge types (Image, Spatial).
- Key files: `internal/base.py` (Abstract Reasoner), `image_classifier/`, `spatial/`.

**src/hcaptcha_challenger/skills/:**
- Purpose: Decouples prompt engineering from the core logic.
- Contains: Prompt templates (Markdown) and matching rules (YAML).
- Key files: `manager.py`, `rules.yaml`, `library/`.

**src/hcaptcha_challenger/cli/:**
- Purpose: Provides a user-friendly interface for manual operations.
- Contains: Typer-based command definitions.
- Key files: `main.py`, `solver.py`, `dataset.py`.

**src/hcaptcha_challenger/helper/:**
- Purpose: Low-level UI manipulation and artifact generation.
- Contains: Scripts for coordinate grids, rasterization, and video conversion.
- Key files: `create_coordinate_grid.py`, `visualize_attention_points.py`.

## Key File Locations

**Entry Points:**
- `src/hcaptcha_challenger/cli/main.py`: Entry point for the `hc` command.
- `src/hcaptcha_challenger/agent/challenger.py`: Main API for programmatic usage (`AgentV`).

**Configuration:**
- `src/hcaptcha_challenger/agent/config.py`: Defines all environment variables and default settings.
- `pyproject.toml`: Defines dependencies and build system.

**Core Logic:**
- `src/hcaptcha_challenger/agent/robotic.py`: Implementation of `RoboticArm` (the browser interaction bridge).
- `src/hcaptcha_challenger/models.py`: Central repository for all Pydantic schemas.

**Testing:**
- `tests/`: Contains both unit tests for tools and integration tests using real artifacts.
- `tests/challenge_view/`: Artifacts used for visual regression and tool testing.

## Naming Conventions

**Files:**
- `snake_case.py`: standard Python module naming (e.g., `spatial_point_reasoner.py`).
- `.md`: Used for prompt templates in `skills/library/` and tool descriptions.

**Directories:**
- `snake_case/`: standard Python package naming.

## Where to Add New Code

**New Challenge Type:**
1. Add new enum members to `ChallengeTypeEnum` in `src/hcaptcha_challenger/models.py`.
2. Create a new reasoning tool in `src/hcaptcha_challenger/tools/` inheriting from `Reasoner`.
3. Add a prompt template to `src/hcaptcha_challenger/skills/library/` and a rule to `rules.yaml`.
4. Implement the solving flow in `RoboticArm` in `src/hcaptcha_challenger/agent/robotic.py`.
5. Update `AgentV._solve_captcha` in `src/hcaptcha_challenger/agent/challenger.py` to route the new type.

**New LLM Provider:**
1. Implement the `ChatProvider` protocol in `src/hcaptcha_challenger/tools/internal/providers/`.
2. Register/use the new provider in `Reasoner._create_default_provider`.

**New CLI Command:**
1. Define the command in a new or existing module in `src/hcaptcha_challenger/cli/`.
2. Register it with the main app in `src/hcaptcha_challenger/cli/main.py`.

## Special Directories

**src/hcaptcha_challenger/logs/:**
- Purpose: Automated storage of runtime logs.
- Generated: Yes
- Committed: No (usually ignored by `.gitignore`)

**tests/challenge_view/:**
- Purpose: Curated set of captcha images for testing tools.
- Generated: No (collected manually or via `dataset` CLI)
- Committed: Yes

---

*Structure analysis: 2025-05-15*
