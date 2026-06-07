# Codex V8 Pipeline Support Design

## Objective

Add first-class Codex provisioning for Hyperresearch V8 while preserving the current Claude Code behavior as the default. Codex support is opt-in through `hyperresearch install --codex`, including project installs, global installs, and step-only installs.

## Runtime Selection

The install command remains Claude-specific unless `--codex` is present.

- `hyperresearch install`: Claude project install.
- `hyperresearch install --codex`: Codex project install.
- `hyperresearch install --global`: Claude global install.
- `hyperresearch install --global --codex`: Codex global install.
- `hyperresearch install --steps-only .`: Claude step skills only.
- `hyperresearch install --steps-only . --codex`: Codex step skills only.

Claude and Codex generated files must be able to coexist on the same computer and in the same repository without overwriting each other.

## Claude Behavior Preservation

Claude Code remains the default runtime and keeps the current generated surfaces:

- Project docs: `CLAUDE.md`
- Skills: `.claude/skills/...`
- Agents: `.claude/agents/...`
- Settings and hook: `.claude/settings.json` plus `.hyperresearch/hook.js`
- Global install root: `~/.claude/...`
- Step-only install target: `<path>/.claude/skills/...`

Existing Claude tests should continue passing without needing changes to their expectations.

## Codex Project Install

`hyperresearch install --codex <path>` initializes or reuses the vault, then provisions Codex-specific files:

- Project docs: inject or update a Hyperresearch section in `AGENTS.md`.
- Entry skill: `.agents/skills/hyperresearch/SKILL.md`.
- Step skills: all 16 V8 step skills under `.agents/skills/hyperresearch-N-name/SKILL.md`.
- Custom agents: Codex-facing custom agent TOML files under `.codex/agents/`.
- Config and hooks: `.codex/config.toml` and/or `.codex/hooks.json` only when the implementation needs Codex-native project configuration or lifecycle enforcement.

Codex project installation must not modify `.claude/`, `CLAUDE.md`, or Claude settings. Codex project-local config, hooks, and custom agents load only when the project `.codex/` layer is trusted by Codex, so generated instructions and CLI output must mention that trust requirement when those files are installed.

## Codex Global Install

`hyperresearch install --global --codex` installs Codex user-level assets into documented Codex locations, separate from `~/.claude`:

- Global instructions: `~/.codex/AGENTS.md`.
- Global skills: `$HOME/.agents/skills/...`.
- Global custom agents: `~/.codex/agents/...`.
- Global config and hooks, if needed: `~/.codex/config.toml` and/or `~/.codex/hooks.json`.

Global Codex install must not write to `~/.claude`.

## Codex Step-Only Install

`hyperresearch install --steps-only <path> --codex` installs only the 16 V8 step skills to `<path>/.agents/skills/...`.

This mirrors the Claude lazy bootstrap behavior but targets Codex paths. It should be idempotent and should not initialize a vault, inject docs, install agents, or touch `.claude/`.

## Shared Prompt Source

The 16 step skills must continue to come from the canonical source files in `src/hyperresearch/skills/*.md`. The Codex installer may apply a small runtime adaptation layer when copied text names Claude-specific paths or mechanics, but it must not hand-duplicate the 16 prompts.

The adaptation layer must explicitly translate Claude-specific mechanics to Codex mechanics:

- Claude `.claude/skills/...` bootstrap paths become Codex `.agents/skills/...` paths.
- Literal Claude `Skill(skill: "hyperresearch-N-name")` instructions become Codex skill-invocation wording, such as invoking the `$hyperresearch-N-name` skill or selecting it through `/skills`.
- Claude `Task` subagent spawn templates become Codex instructions to spawn the named custom agent, run required agents in parallel where the V8 pipeline requires parallelism, wait for all results, and summarize or persist each result according to the step contract.
- Claude tool names in prose may remain only when they describe the original architecture for contrast; operative instructions must use Codex terminology.

Load-bearing invariants that must survive Codex adaptation:

- Entry router and 16-step V8 architecture.
- Light sequence: `1 -> 2 -> 10 -> 15 -> 16`.
- Full sequence: `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14 -> 15 -> 16`.
- Canonical query file: `research/query-<vault_tag>.md`.
- Artifact paths used by lint rules.
- Tier gates.
- Required subagent roster and role boundaries.
- Parallelism where the Claude pipeline requires it.
- Patch-only revision discipline after the final report exists.
- Final integrity and lint gates.

## Codex Subagent Definitions

Codex subagent definitions should be generated from the existing Claude subagent prompt constants initially, with path and runtime labels adapted only where necessary.

Each Codex custom agent must be a standalone TOML file under `.codex/agents/` for project installs or `~/.codex/agents/` for global installs. Each file must define the documented required fields:

- `name`
- `description`
- `developer_instructions`

Optional fields such as `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` may be used when they preserve V8 role quality or reduce accidental tool misuse.

Tests must verify that the Codex-facing definitions preserve:

- Role names and pipeline positions.
- Model tier intent such as Opus-equivalent critic and synthesis roles and Sonnet-equivalent fetch/depth roles.
- Tool restriction intent, especially patcher and polish auditor being edit-only.
- Required artifact paths.
- Canonical research query usage.
- Report-back contracts.

Claude `tools:` frontmatter does not have a documented one-to-one Codex custom-agent equivalent. The Codex port must therefore separate two concepts:

- **Prompt-level restriction intent:** custom agent `developer_instructions` must preserve the role's allowed and forbidden behaviors, especially patcher and polish auditor being edit-only and never regenerating whole reports.
- **Mechanical enforcement:** when the implementation adds hooks, rules, sandbox settings, or MCP/tool configuration to enforce restrictions, it must use documented Codex surfaces such as `.codex/hooks.json`, `.codex/config.toml`, `~/.codex/hooks.json`, `~/.codex/config.toml`, or Codex rules. If mechanical enforcement is not complete for a role, prompts and CLI output must not claim exact tool-lock parity with Claude.

Prompt text must not claim benchmark parity or full Codex equivalence until there is benchmark evidence and an end-to-end Codex run.

## Codex Project Instructions

The `AGENTS.md` injected section should be concise and marked with Codex-specific start/end markers so it can update idempotently without overwriting user content.

The section must tell Codex:

- Run research sessions through the Hyperresearch entry skill.
- Treat the entry skill as a router, not as the full procedure.
- Load step procedures fresh from `.agents/skills/...`.
- Use the canonical query file as gospel.
- Preserve markdown as truth and SQLite as cache.
- Preserve patch-only revision after final report creation.
- Run the final lint gates before declaring completion.
- Treat `.codex/` project config, hooks, and custom agents as active only after Codex trusts the project.

## Codex Hooks and Settings

Codex hooks and settings must use documented Codex configuration surfaces, not Claude settings.

Project-scoped Codex config and hooks:

- `.codex/config.toml`
- `.codex/hooks.json`

User-scoped Codex config and hooks:

- `~/.codex/config.toml`
- `~/.codex/hooks.json`

Hooks are enabled by the Codex `features.hooks` configuration key and non-managed command hooks require Codex trust review before they run. Project-local hooks load only when the project `.codex/` layer is trusted.

If Hyperresearch installs Codex hooks, they should be narrowly scoped to the relevant lifecycle events and tool matchers. Examples of relevant Codex hook matchers include `Bash`, `^apply_patch$`, and `Edit|Write` for events such as `PreToolUse`, `PostToolUse`, `PermissionRequest`, `SubagentStart`, and `SubagentStop`.

The implementation must not port Claude `.claude/settings.json` directly to Codex. Settings migration must target Codex `config.toml` or hooks JSON.

## Testing Strategy

Add focused Codex provisioning tests near the existing Claude hook tests.

Minimum expected coverage:

- `hyperresearch install --codex` creates `AGENTS.md`, `.agents/skills/hyperresearch/SKILL.md`, all 16 step skills, and Codex subagent definitions.
- Codex project instruction injection is idempotent and does not modify `CLAUDE.md`.
- `--steps-only --codex` installs all 16 step skills under `.agents/skills/...` and does not touch `.claude/`.
- `--global --codex` writes global instructions to `~/.codex/AGENTS.md`, global skills to `$HOME/.agents/skills/...`, global custom agents to `~/.codex/agents/...`, and does not touch `~/.claude`.
- Codex entry skill references all required step skills, tier sequences, canonical query file, and patching invariant.
- Codex-adapted step skills do not contain operative Claude-only bootstrap paths such as `.claude/skills/...`.
- Codex-adapted step skills translate operative `Skill(...)` and `Task` instructions into Codex skill invocation and custom-agent spawning instructions.
- Codex subagent definitions preserve role, model tier intent, tool restriction intent, and required artifact paths.
- Codex custom agent files use documented TOML fields, including `name`, `description`, and `developer_instructions`.
- Any installed Codex hooks or config files use `.codex` / `~/.codex` surfaces and documented hook event shapes.
- Existing Claude install tests still pass.
- CLI smoke tests still pass.

## Non-Goals

- Do not remove, rename, or weaken Claude Code files.
- Do not rewrite the 16 step prompts by hand.
- Do not change benchmark claims in `README.md`.
- Do not claim Codex benchmark parity.
- Do not make SQLite authoritative for note content.
- Do not reduce adversarial steps, source-reading requirements, critic coverage, or required parallelism.
