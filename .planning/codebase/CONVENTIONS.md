# Conventions

## Coding Standards
- **Line Length**: Limited to 100 characters.
- **Typing**: Extensive use of Python type hints to ensure reliability and aid in static analysis.
- **String Normalization**: Skipped string normalization (configured in `black`).

## Formatting & Linting
- **Formatter**: `black`
  - Targets: `py310`, `py311`, `py312`, `py313`
  - Excludes: `archive`, `.venv`, `docs/.*\.ipynb`
- **Linter**: `ruff`
  - Excludes: `archive/`, `*.ipynb`

## Git & Versioning
- **Versioning**: Uses `uv-dynamic-versioning` synchronized with git tags.
- **Commit Style**: Project appears to use standard commit conventions, possibly following conventional commits given the `CHANGELOG.md` presence and CI workflows.

*(Note: The `archive` component has been explicitly excluded from this map.)*
