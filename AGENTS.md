# AGENTS.md

## Mission

This repository is Hyperresearch: a Python CLI, MCP server, and agent harness for disciplined deep research with persistent markdown provenance. The current production harness targets Claude Code through `.claude/skills`, `.claude/agents`, `CLAUDE.md`, and Claude-specific `Skill` / `Task` mechanics.

The active development objective is to add first-class Codex support for the full advertised Hyperresearch V8 16-step adversarial pipeline, with minimal code changes and no intentional quality loss versus the Claude Code implementation. Any quality difference should come only from model/runtime differences, not from a weaker port.

## Non-Negotiable Product Invariants

- Preserve Claude Code behavior. Codex support must be additive unless a change is explicitly required and tested for both runtimes.
- Preserve the V8 architecture: entry router, 16 step procedures, tier gates, canonical query file, artifact paths, subagent roster, patch-only revision discipline, and final lint gates.
- Preserve "patch, never regenerate" after the final report exists. Patcher and polish agents must remain unable to overwrite or regenerate the report wholesale.
- Preserve the canonical research query as gospel. Every downstream step and subagent must read the persisted `research/query-<vault_tag>.md`.
- Preserve markdown as truth and SQLite as cache. Do not make the database authoritative for note content.
- Prefer the smallest compatibility layer that maps Claude Code concepts to Codex concepts. Avoid duplicating 16 prompts by hand if generation or shared source material can keep the two runtimes identical.
- Do not weaken prompts, remove adversarial steps, lower source-reading requirements, skip critics, or reduce parallelism for convenience.
- Do not claim benchmark parity without benchmark evidence.

## Success Criteria

- `hyperresearch install` or a new Codex-specific install path can provision Codex project instructions, skills, subagents/workflows, and hooks needed to run the V8 pipeline in Codex.
- Codex can run the same light/full tier sequence as Claude Code:
  - light: 1 -> 2 -> 10 -> 15 -> 16
  - full: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14 -> 15 -> 16
- The Codex port keeps the same artifact contract used by existing lint rules.
- Existing Claude Code tests keep passing.
- New Codex provisioning tests cover generated `AGENTS.md`, `.agents/skills`, Codex-facing hooks/config, and any Codex subagent definitions.
- Benchmark success is measured against the `Ayanami0730/deep_research_bench` methodology referenced by the README benchmark graphic. Codex results should be close to Hyperresearch Claude Code results on comparable prompts.

## Repository Facts

- Origin remote: `https://github.com/hossainzarif23/hyperresearch.git`
- Upstream remote: `https://github.com/jordan-gibbs/hyperresearch.git`
- Package: `hyperresearch`
- Python support: `>=3.11,<3.14`
- CLI entrypoints: `hyperresearch` and `hpr`
- Source root: `src/hyperresearch`
- Tests root: `tests`
- Current Claude install logic: `src/hyperresearch/core/hooks.py`
- Current agent-doc injection: `src/hyperresearch/core/agent_docs.py`
- Current step prompt sources: `src/hyperresearch/skills/*.md`

## Environment

Use the repository virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[all,dev]"
```

Use `.venv` commands for verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m hyperresearch --help
```

If Windows console encoding breaks package metadata output, set:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

## Superpowers Workflow

Use the original `obra/superpowers` workflow for this development. Superpowers is a methodology, not a loose checklist. The agent must check for relevant skills before every task, and applicable skills are mandatory.

Follow this sequence for feature work:

1. **Brainstorm before code.** Use `brainstorming` when the request is still a rough idea or design problem. Ask targeted questions, explore alternatives, present the design in readable sections, and get human approval before implementation planning.
2. **Create an isolated workspace after design approval.** Use `using-git-worktrees` before implementation work. Create or verify a separate branch/worktree, run project setup, and verify a clean baseline.
3. **Write the implementation plan from the approved design.** Use `writing-plans`. Save the plan under `docs/superpowers/plans/`. The plan must break work into 2-5 minute tasks with exact files, concrete code or command snippets, and verification steps. Get human approval before executing the implementation plan.
4. **Execute the written plan with subagents.** Always use `subagent-driven-development` to execute implementation plans: dispatch a fresh subagent per task, then perform the required two-stage review for spec compliance and code quality. Do not silently fall back to inline execution.

   If subagents cannot be created or used, stop before implementation and report the exact blocker, such as missing subagent tooling, unavailable plugin/runtime support, failed subagent creation, or permission/configuration limits. Explain why that prevents following `subagent-driven-development`, then ask whether to proceed with `executing-plans` as an explicit fallback. Only use `executing-plans` after the user approves that fallback.

   Subagent model policy for this Codex port work: use GPT-5.5 with medium reasoning for coding/implementation worker subagents. Use GPT-5.4-mini with medium reasoning for non-coding subagents, including spec-compliance reviewers, code-quality reviewers, explorer/research agents, and other read-only review roles.
5. **Use TDD during implementation.** Use `test-driven-development` for behavior changes: write the failing test, see it fail, write the minimum implementation, see it pass, refactor, and commit. If production code was written before the test, delete or revert it and restart the red/green cycle.
6. **Review between tasks.** Under `subagent-driven-development`, every task must pass spec-compliance review before code-quality review. Open review issues block progress until fixed. Use `requesting-code-review` only when an additional human-facing or external review is needed.
7. **Finish the branch deliberately.** Use `finishing-a-development-branch` when planned tasks are complete. Run fresh verification, then present the options to merge, open a PR, keep the branch, or discard the worktree.

Use `systematic-debugging` for bugs and failing tests. Use `verification-before-completion` before any claim that work is complete, fixed, passing, or ready for PR. Evidence comes before status claims.

Do not skip the workflow because a task seems small. Do not jump from idea directly to implementation unless the request is truly a narrow mechanical edit and no Superpowers skill applies.

## Codex Port Strategy

Treat Codex support as a compatibility layer over the existing V8 source material.

Expected mapping:

- Claude `CLAUDE.md` project memory -> Codex `AGENTS.md` project instructions.
- Claude `.claude/skills/<name>/SKILL.md` -> Codex repo skills under `.agents/skills/<name>/SKILL.md`.
- Claude slash command `/hyperresearch` -> Codex skill invocation and/or Codex custom prompt surface, depending on the smallest reliable supported surface.
- Claude `Task` subagents -> Codex subagent workflows or configured Codex subagents with equivalent prompts, model strength, tool limits, and report-back contracts.
- Claude PreToolUse hook -> Codex hooks/config if needed for mechanical enforcement.
- Claude tool locks -> Codex-side tool restrictions, hook checks, or prompt-enforced contracts only if Codex has no exact equivalent.

When implementing, first look for a shared prompt source or generator path so Claude and Codex prompts cannot drift. If separate output files are necessary, tests must prove the installed Codex prompts contain the same load-bearing invariants as the Claude prompts.

## Quality Bar For Codex Equivalence

- Use the strongest available Codex model/reasoning configuration for Opus-equivalent roles unless the user explicitly requests a cost-saving mode.
- Use cheaper/faster Codex workers only where the Claude implementation already uses lower-cost workers and the role is read-heavy or fetch-heavy.
- Preserve parallel subagent execution where the Claude pipeline requires it.
- Preserve per-agent role boundaries. Fetchers fetch, critics critique, patchers patch, synthesizers synthesize.
- Preserve fresh-context step loading. The Codex implementation must avoid one giant always-loaded prompt if that would reintroduce context rot.
- Preserve explicit artifact recovery after compaction or resumed sessions.

## Development Rules

- Read the existing code before changing it.
- Prefer narrow edits in existing modules over broad rewrites.
- Keep public CLI behavior backward-compatible unless a plan explicitly says otherwise.
- Add tests before or alongside implementation for every new behavior.
- Do not create new production dependencies unless they are clearly needed for Codex integration.
- Keep generated instructions concise and structured. Long durable instruction files reduce adherence.
- Do not edit benchmark claims in `README.md` unless benchmark evidence has changed.
- Do not remove or rename existing Claude files, agents, or skills as part of Codex support.
- Do not commit virtual environments, generated vaults, caches, local benchmark outputs, or credentials.

## Test Expectations

For any Codex integration change, add focused tests for the changed surface. Prefer tests similar to `tests/test_core/test_hooks.py`.

Minimum expected coverage:

- Codex project instruction generation is idempotent.
- Codex skill installation creates all 16 step skills from the canonical source material.
- Codex entry skill/router references all required step skills and the patching invariant.
- Codex subagent definitions preserve role, model tier intent, tool restrictions, and required artifact paths.
- Claude install tests still pass.
- CLI smoke tests still pass.

Run the narrow test first, then the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_hooks.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

## Benchmark Expectations

When benchmark work begins:

- Read `Ayanami0730/deep_research_bench` directly before implementing benchmark automation.
- Keep benchmark setup reproducible and separated from normal unit tests.
- Record model, runtime, prompt, tier, provider, date, and exact commit SHA.
- Compare Codex output to the Claude Code Hyperresearch baseline using the same benchmark protocol wherever possible.
- Treat benchmark parity as empirical, not assumed.

## PR Discipline

- Work on a branch intended for upstream PR review.
- Keep commits focused and reviewable.
- Include a concise PR summary of behavior, test coverage, and benchmark status.
- If benchmark parity has not yet been run, say that explicitly.
- Never describe Codex integration as complete until the full 16-step pipeline has been exercised end to end in Codex and verified against the artifact/lint contract.
