# Claude Code — Project Guide

## Package management

Use `uv`, never `pip` directly. Install deps with `uv sync`; run tools with `uv run <tool>`. Add packages with `uv add`.

## Code quality

All Python must pass `ruff check` and `mypy --strict` before committing. No exceptions, no `# type: ignore` without a comment explaining why. The CI blocks on both.

## Plugin pattern

Swappable components (tone detector, timing decoder, interpreter) each have an ABC in `plugins/base.py`. Concrete implementations register themselves with a decorator from `plugins/factory.py`. The factory reads the active implementation name from `config.toml` at startup. When adding a new plugin: subclass the right ABC, apply the registration decorator, and update `config.toml` if it should become the default.

## Pipeline data flow

Each pipeline stage communicates through typed DTOs defined in `pipeline/types.py`. Prefer adding to or extending those types over passing raw dicts or untyped values between stages.

## Configuration

`config.toml` holds committed defaults. `config.local.toml` is gitignored and is the right place for local overrides. Environment variables (prefixed per pydantic-settings) override both for deployment.

## What is not yet implemented

Check `docs/status.md` before starting work on a new component — it tracks what is scaffolded versus what still needs to be built.
