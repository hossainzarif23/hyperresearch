# Codex AGENTS.md Parity Design

## Goal

Generated Codex `AGENTS.md` files must be Codex-native project instructions that preserve the same load-bearing runtime guidance currently generated in Claude Code `CLAUDE.md`.

## Problem

The current Codex install path writes a thin `AGENTS.md` section that only points at `.agents/skills`, `.codex/agents`, route sequences, canonical query persistence, markdown truth, and patch-only revision. Claude Code installs a much richer `CLAUDE.md` with operational guidance for the research workflow, fetch discipline, academic API ordering, PDF handling, vault search, assets, authenticated crawling, curation, and path conventions.

That mismatch is a Codex port-quality gap. It makes a Codex vault less self-describing than a Claude vault and increases the risk that Codex starts a deep research run without important runtime expectations in durable project instructions.

## Source Guidance

The OpenAI Codex manual says `AGENTS.md` is the durable project-instruction surface for repository conventions, commands, verification steps, and expectations. It also documents `.agents/skills` as progressive-disclosure reusable workflows and `.codex/agents/*.toml` as project-scoped custom agent definitions.

Therefore, `AGENTS.md` should carry durable runtime conventions and commands, while the entry skill and step skills carry detailed step procedures and custom agents carry role-specific behavior.

## Recommended Architecture

Introduce a shared renderer in `src/hyperresearch/core/agent_docs.py` that builds project instruction blurbs from common sections plus runtime-specific wording.

Claude output remains behavior-compatible:

- `CLAUDE.md`
- `/hyperresearch <query>`
- `.claude/skills/hyperresearch/SKILL.md`
- Claude `Skill` and `Task` mechanics

Codex output becomes equivalent but Codex-native:

- `AGENTS.md`
- `$hyperresearch <query>` or explicit `$hyperresearch` skill invocation
- `.agents/skills/hyperresearch/SKILL.md`
- Codex skill progressive disclosure
- `.codex/agents/*.toml` custom agents
- Codex custom-agent spawns instead of Claude `Task` calls

## Required Codex AGENTS.md Content

The generated Codex section must include the same substantive guidance as Claude `CLAUDE.md`:

- exact CLI path
- current-working-directory path convention
- deep research entrypoint
- entry skill/router location
- 16 step skills and fresh loading
- light and full tier behavior
- source fetch discipline
- what skill files own
- canonical research query handling
- academic API-first guidance
- PDF fetching guidance
- vault search commands
- asset and screenshot commands
- authenticated crawling guidance
- mandatory curation pass
- note lifecycle and summary quality
- markdown/vault conventions
- patch-never-regenerate invariant after final report exists

The Codex version must not leak Claude-only paths or slash-command-only wording as the primary instruction surface.

## Test Strategy

Add focused tests for Codex project doc generation. Tests should assert load-bearing parity by checking required sections and phrases, not byte-for-byte equality. Existing Claude docs and install tests must keep passing.

Expected focused verification:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py tests\test_core\test_codex_hooks.py tests\test_cli\test_install_codex.py tests\test_core\test_hooks.py -q
..\..\.venv\Scripts\python.exe -m ruff check src tests
```

Full verification remains:

```powershell
..\..\.venv\Scripts\python.exe -m pytest -q
..\..\.venv\Scripts\python.exe -m ruff check src tests
```

`mypy src` is currently not a clean baseline and should not be used as the decisive gate for this focused fix unless the existing repository type errors are separately addressed.

## Non-Goals

- Do not change Claude Code behavior except through shared rendering that preserves generated Claude output semantics.
- Do not edit benchmark claims.
- Do not change the 16 step prompt sources.
- Do not add new production dependencies.
- Do not run a real deep research query as part of this code fix.
