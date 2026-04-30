# Codebase Structure

**Analysis Date:** 2026-04-30

## Directory Layout

```text
hcaptcha-challenger/
├── src/                     # Python package source
│   └── hcaptcha_challenger/ # Main runtime package
├── tests/                   # Active test suite
├── docs/                    # End-user docs and notebooks
├── examples/                # Usage samples and demos
├── archive/                 # Legacy code, experiments, old tests
├── docker/                  # Containerization assets
├── .planning/               # GSD planning + codebase map artifacts
└── pyproject.toml           # Project metadata, deps, tooling config
```

## Directory Purposes

**`src/hcaptcha_challenger`:**
- Purpose: Production runtime package.
- Contains: CLI commands, browser agent, tools, models, helper and skill systems.
- Key files: `src/hcaptcha_challenger/__init__.py`, `src/hcaptcha_challenger/models.py`, `src/hcaptcha_challenger/utils.py`

**`src/hcaptcha_challenger/agent`:**
- Purpose: Core challenge orchestration and browser interaction.
- Contains: solver control loop, robotic action primitives, agent settings.
- Key files: `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/agent/robotic.py`, `src/hcaptcha_challenger/agent/config.py`

**`src/hcaptcha_challenger/tools`:**
- Purpose: Tool façade + challenge-specific reasoners.
- Contains: challenge router, image classifier, spatial reasoners, provider abstractions.
- Key files: `src/hcaptcha_challenger/tools/__init__.py`, `src/hcaptcha_challenger/tools/internal/base.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`

**`src/hcaptcha_challenger/cli`:**
- Purpose: Console command entrypoints.
- Contains: top-level Typer app, dataset/solver command modules.
- Key files: `src/hcaptcha_challenger/cli/main.py`, `src/hcaptcha_challenger/cli/dataset.py`, `src/hcaptcha_challenger/cli/solver.py`

**`src/hcaptcha_challenger/helper`:**
- Purpose: Supporting image/cost utilities reused by CLI and agent flows.
- Contains: coordinate-grid generation, visualization, cost calculator.
- Key files: `src/hcaptcha_challenger/helper/create_coordinate_grid.py`, `src/hcaptcha_challenger/helper/cost_calculator.py`

**`src/hcaptcha_challenger/skills`:**
- Purpose: Rule-driven prompt template matching for challenge prompts.
- Contains: manifest schema, rule manager, markdown skill library.
- Key files: `src/hcaptcha_challenger/skills/manager.py`, `src/hcaptcha_challenger/skills/schema.py`, `src/hcaptcha_challenger/skills/rules.yaml`

**`tests`:**
- Purpose: Test coverage for helper and tool behavior.
- Contains: tool tests, spatial tests, helper tests, model/schema tests.
- Key files: `tests/test_tools_challenge_classifier.py`, `tests/test_tools_spatial_path_reasoning.py`, `tests/test_helper_create_coordinate_grid.py`

## Key File Locations

**Entry Points:**
- `pyproject.toml`: Registers `hc = hcaptcha_challenger.cli.main:main`.
- `src/hcaptcha_challenger/cli/main.py`: Root CLI app and command wiring.
- `src/hcaptcha_challenger/__init__.py`: Public import surface and runtime log initialization.

**Configuration:**
- `pyproject.toml`: Dependency, build, lint/test tool configuration.
- `setup.py`: Legacy packaging compatibility.
- `src/hcaptcha_challenger/agent/config.py`: Runtime settings and env-backed secrets.

**Core Logic:**
- `src/hcaptcha_challenger/agent/challenger.py`: Captcha response lifecycle and queue handling.
- `src/hcaptcha_challenger/agent/robotic.py`: Main challenge-solving action pipeline.
- `src/hcaptcha_challenger/models.py`: Canonical data contracts and challenge enums.
- `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`: External model call adapter.

**Testing:**
- `tests/`: Primary automated test folder configured by `[tool.pytest.ini_options]`.
- `archive/tests/`: Historical tests (treat as legacy/non-authoritative for new work).

## Naming Conventions

**Files:**
- Snake_case module naming across production and tests (example: `mouse_config.py`, `test_tools_common.py`).
- Test files use `test_*.py` prefix (example: `test_tools_image_classifier.py`).

**Directories:**
- Lowercase domain-based directories under package root (example: `agent`, `tools`, `skills`).
- Tool categories are nested as nouns by capability (example: `tools/challenge_router`, `tools/spatial`).

## Where to Add New Code

**New Feature:**
- Primary code: `src/hcaptcha_challenger/agent/` for orchestration changes, or `src/hcaptcha_challenger/tools/` for new reasoning capabilities.
- Tests: `tests/` with `test_<feature>.py` naming and import from public package path where possible.

**New Component/Module:**
- Implementation: `src/hcaptcha_challenger/<domain>/` where `<domain>` matches ownership (`helper`, `tools`, `skills`, `agent`).

**Utilities:**
- Shared helpers: `src/hcaptcha_challenger/helper/` for reusable non-provider/non-agent helpers.
- Cross-cutting typed models: `src/hcaptcha_challenger/models.py` (or split submodule if model surface becomes large).

## Special Directories

**`archive/`:**
- Purpose: Legacy implementation snapshots, old tests, and exploratory code.
- Generated: No.
- Committed: Yes.

**`tmp/`:**
- Purpose: Runtime output workspace (`.cache`, challenge artifacts, model answers).
- Generated: Yes.
- Committed: No (excluded by `.gitignore` patterns).

**`.planning/`:**
- Purpose: GSD planning and generated architecture/quality map docs.
- Generated: Yes.
- Committed: Project-dependent (currently present in repository workspace).

**`src/hcaptcha_challenger/logs/`:**
- Purpose: Runtime log sink configured by package import initialization.
- Generated: Yes.
- Committed: No (runtime artifact directory).

---

*Structure analysis: 2026-04-30*
