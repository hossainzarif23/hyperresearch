# Codex AGENTS.md Parity Design

## Goal

Generated Codex `AGENTS.md` files must be Codex-native project instructions that preserve the same load-bearing runtime guidance currently generated in Claude Code `CLAUDE.md`.

## Problem

The current implementation maintains `CLAUDE.md` and `AGENTS.md` guidance as two independent string constants in `src/hyperresearch/core/agent_docs.py`.

That is not maintainable:

- Claude gets a rich `CLAUDE.md` blurb with operational guidance for the research workflow, fetch discipline, academic API ordering, PDF handling, vault search, assets, authenticated crawling, curation, and path conventions.
- Codex gets a short `AGENTS.md` stub that only points at `.agents/skills`, `.codex/agents`, route sequences, canonical query persistence, markdown truth, and patch-only revision.
- Future feature changes can update Claude guidance without updating Codex guidance.
- Tests check for a few Codex phrases but do not prove equivalence.

The product requirement is additive Codex support with no intentional quality loss versus Claude Code. Separate hand-authored project docs violate that requirement.

## Source Guidance

The OpenAI Codex manual defines `AGENTS.md` as the durable project-instruction surface for repository conventions, commands, verification steps, and expectations. It defines `.agents/skills` as progressive-disclosure reusable workflows and `.codex/agents/*.toml` as project-scoped custom-agent definitions.

Therefore:

- `AGENTS.md` should carry durable Hyperresearch runtime conventions and commands.
- `.agents/skills/*/SKILL.md` should carry detailed step procedures.
- `.codex/agents/*.toml` should carry Codex custom-agent role behavior.

`AGENTS.md` should not be a thin pointer when Claude `CLAUDE.md` carries substantive workflow guidance.

## Approved Architecture

Move the canonical project-doc source out of Python strings and into a package markdown template:

```text
src/hyperresearch/templates/agent_docs/hyperresearch_project.md
```

This file is the single source for durable project runtime guidance. It contains the shared prose and explicit runtime placeholders such as:

```md
{marker}
## {title}

**CLI path: `{hpr}`** ...

**Run a research session with `{research_entrypoint}`.**

The entry skill lives at `{entry_skill_path}`.
The step skills live under `{step_skill_root}`.
Step procedures are loaded fresh via {step_loading_mechanic}.
Subagents are delegated through {subagent_mechanic}.
{end_marker}
```

`src/hyperresearch/core/agent_docs.py` should own only:

- loading the template with `importlib.resources`
- rendering the Claude context
- rendering the Codex context
- injecting the rendered section into `CLAUDE.md` or `AGENTS.md`

This avoids copying Claude text and then regex-rewriting it into Codex. It also avoids maintaining two independent long strings.

## Runtime Rendering

Claude rendering should preserve current behavior:

- output file: `CLAUDE.md`
- marker: `<!-- hyperresearch:start -->`
- entrypoint: `/hyperresearch <query>`
- entry skill: `.claude/skills/hyperresearch/SKILL.md`
- step skill root: `.claude/skills`
- step loading mechanic: Claude `Skill(...)`
- subagent mechanic: Claude `Task`

Codex rendering should be Codex-native:

- output file: `AGENTS.md`
- marker: `<!-- hyperresearch-codex:start -->`
- entrypoint: `$hyperresearch <query>` or explicit `$hyperresearch` skill invocation
- entry skill: `.agents/skills/hyperresearch/SKILL.md`
- step skill root: `.agents/skills`
- step loading mechanic: Codex skill invocation / progressive disclosure
- subagent mechanic: Codex custom-agent spawns using `.codex/agents/*.toml`

The generated Codex doc must not use `.claude/skills`, `/hyperresearch`, or `Task call` as operative instructions.

## Required Shared Content

The template must preserve the same substantive guidance currently present in Claude `CLAUDE.md`:

- exact CLI path
- current-working-directory path convention
- research session entrypoint
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
- final report patch-only revision invariant

The template may add Codex-specific trust/config wording only through runtime-specific placeholders or clearly scoped runtime notes.

## Refresh Commands

Fresh installs already choose runtime through `hyperresearch install --codex` versus default Claude install.

Existing doc refresh commands are Claude-only. Add explicit runtime options:

```powershell
hyperresearch config agent-docs --claude
hyperresearch config agent-docs --codex
hyperresearch repair --docs --claude
hyperresearch repair --docs --codex
```

Defaults remain backward-compatible:

- `hyperresearch config agent-docs` updates Claude `CLAUDE.md`.
- `hyperresearch repair --docs` updates Claude `CLAUDE.md`.
- Codex docs update only when `--codex` is passed.
- `--claude` and `--codex` are mutually exclusive.

## Deterministic Tests

Add tests that render both runtime docs from the same template and assert semantic structure:

- both rendered docs contain the same canonical section headings
- both rendered docs contain required shared invariants
- Claude rendering contains Claude-specific paths and mechanics
- Codex rendering contains Codex-specific paths and mechanics
- Codex rendering does not leak Claude-only operative instructions
- existing Codex install tests still pass
- existing Claude install tests still pass
- `config agent-docs --codex` updates `AGENTS.md`
- `repair --docs --codex` updates `AGENTS.md`

These tests are the durable guardrail for future feature changes.

## Agent-Based Equivalence Review

Add an advisory review step to the verification procedure:

1. Generate a temporary Claude `CLAUDE.md`.
2. Generate a temporary Codex `AGENTS.md`.
3. Spawn a Codex review subagent.
4. Ask it to judge whether the documents are semantically equivalent except for runtime-specific mechanics.

This review catches wording and omission problems that deterministic tests may miss. It must not replace deterministic tests because model judgment is not stable enough as the only correctness gate.

## Packaging

The template lives under the `hyperresearch` package tree so it is included with package builds. `agent_docs.py` should load it via `importlib.resources`, following the existing pattern used for bundled skill markdown in `src/hyperresearch/core/hooks.py`.

## Non-Goals

- Do not rewrite the 16 step prompt sources.
- Do not change benchmark claims.
- Do not claim Codex benchmark parity.
- Do not add new production dependencies.
- Do not port Claude hooks/settings directly to Codex.
- Do not run a real deep research query as part of this code fix.
