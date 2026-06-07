# Codex V8 Pipeline Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in Codex provisioning for the Hyperresearch V8 16-step pipeline while preserving Claude Code as the default install target.

**Architecture:** Keep Claude installers unchanged and add a Codex-specific compatibility layer. Codex project installs write `AGENTS.md`, `.agents/skills/...`, and `.codex/agents/...`; Codex global installs write `~/.codex/AGENTS.md`, `$HOME/.agents/skills/...`, and `~/.codex/agents/...`. Codex step skills are adapted from the canonical `src/hyperresearch/skills/*.md` sources at install time so Claude and Codex prompts cannot drift.

**Tech Stack:** Python 3.11, Typer CLI, pytest, stdlib `pathlib`, `json`, `re`, and `tomllib` for validating generated TOML in tests.

**Baseline:** In isolated worktree `E:\Deep Research\hyperresearch\.worktrees\codex-v8-support`, `pytest -q`, `ruff check src tests`, and `python -m hyperresearch --help` pass. `mypy src` fails before implementation with existing unrelated strict-typing issues across 37 files; do not fix those in this branch.

---

## File Structure

- Modify `src/hyperresearch/core/agent_docs.py`: add Codex-specific `AGENTS.md` marker constants, blurb, and `inject_codex_agent_docs()`.
- Create `src/hyperresearch/core/codex_hooks.py`: Codex skill adaptation, Codex custom-agent TOML generation, project/global/steps-only Codex installers.
- Modify `src/hyperresearch/cli/install.py`: add `--codex` option and route project/global/steps-only installs to the Codex installer.
- Create `tests/test_core/test_codex_agent_docs.py`: idempotent `AGENTS.md` injection tests.
- Create `tests/test_core/test_codex_hooks.py`: Codex skill, custom-agent, and project/global installer tests.
- Create `tests/test_cli/test_install_codex.py`: CLI routing tests for `--codex`, `--steps-only --codex`, and JSON output.

---

### Task 1: Codex AGENTS.md Injection

**Files:**
- Modify: `src/hyperresearch/core/agent_docs.py`
- Create: `tests/test_core/test_codex_agent_docs.py`

- [ ] **Step 1: Write failing Codex docs tests**

Create `tests/test_core/test_codex_agent_docs.py`:

```python
from __future__ import annotations

from hyperresearch.core.agent_docs import (
    CODEX_HYPERRESEARCH_SECTION_END,
    CODEX_HYPERRESEARCH_SECTION_MARKER,
    inject_codex_agent_docs,
)


def test_inject_codex_agent_docs_creates_agents_md(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "hyperresearch.core.agent_docs._resolve_executable",
        lambda: r"C:\venv\Scripts\hyperresearch.exe",
    )

    actions = inject_codex_agent_docs(tmp_path)

    assert actions == ["AGENTS.md (created)"]
    agents_path = tmp_path / "AGENTS.md"
    assert agents_path.exists()
    body = agents_path.read_text(encoding="utf-8")
    assert CODEX_HYPERRESEARCH_SECTION_MARKER in body
    assert CODEX_HYPERRESEARCH_SECTION_END in body
    assert ".agents/skills/hyperresearch/SKILL.md" in body
    assert ".codex/agents/" in body
    assert "research/query-<vault_tag>.md" in body
    assert "PATCH, NEVER REGENERATE" in body
    assert "--steps-only . --codex --json" in body
    assert "C:/venv/Scripts/hyperresearch.exe" in body
    assert not (tmp_path / "CLAUDE.md").exists()


def test_inject_codex_agent_docs_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "hyperresearch.core.agent_docs._resolve_executable",
        lambda: "hyperresearch",
    )

    first = inject_codex_agent_docs(tmp_path)
    second = inject_codex_agent_docs(tmp_path)

    assert first == ["AGENTS.md (created)"]
    assert second == []
    body = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert body.count(CODEX_HYPERRESEARCH_SECTION_MARKER) == 1
    assert body.count(CODEX_HYPERRESEARCH_SECTION_END) == 1


def test_inject_codex_agent_docs_preserves_user_content(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "hyperresearch.core.agent_docs._resolve_executable",
        lambda: "hyperresearch",
    )
    agents_path = tmp_path / "AGENTS.md"
    agents_path.write_text("# Existing rules\n\nKeep this.\n", encoding="utf-8")

    actions = inject_codex_agent_docs(tmp_path)

    assert actions == ["AGENTS.md (appended)"]
    body = agents_path.read_text(encoding="utf-8")
    assert body.startswith("# Existing rules\n\nKeep this.")
    assert CODEX_HYPERRESEARCH_SECTION_MARKER in body
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py -q
```

Expected: FAIL with `ImportError` because `CODEX_HYPERRESEARCH_SECTION_MARKER` and `inject_codex_agent_docs` do not exist.

- [ ] **Step 3: Implement Codex docs injection**

In `src/hyperresearch/core/agent_docs.py`, add these constants after the existing Claude marker constants:

```python
CODEX_HYPERRESEARCH_SECTION_MARKER = "<!-- hyperresearch-codex:start -->"
CODEX_HYPERRESEARCH_SECTION_END = "<!-- hyperresearch-codex:end -->"

CODEX_HYPERRESEARCH_BLURB = """
{marker}
## Research Base (hyperresearch for Codex) -- Today is {today}

**CLI path: `{hpr}`** -- use this exact path for every hyperresearch command. It may not be on your system PATH.

This project uses Hyperresearch as a Codex-driven research knowledge base. The `research/` directory contains markdown notes collected from web sources and original research. Markdown files are the source of truth; SQLite is only a cache.

### How to do research

Run a research session by invoking the Codex skill `$hyperresearch` with the user's research query. The entry skill at `.agents/skills/hyperresearch/SKILL.md` is a thin router. The 16 step procedures live in `.agents/skills/hyperresearch-1-decompose/SKILL.md` through `.agents/skills/hyperresearch-16-readability-audit/SKILL.md` and must be loaded fresh when each step runs.

If the step skills are missing, run:

```bash
{hpr} install --steps-only . --codex --json
```

Codex custom agents for Hyperresearch live under `.codex/agents/`. Project-local `.codex/` config, hooks, and custom agents are active only after Codex trusts the project.

### Required V8 routing

- light: `1 -> 2 -> 10 -> 15 -> 16`
- full: `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14 -> 15 -> 16`

The entry skill owns tier classification and routing. Do not skip, reorder, or add steps outside the tier contract.

### Canonical research query

Every run must persist the canonical query at `research/query-<vault_tag>.md`. That file is gospel for every downstream step and every custom agent. Do not paraphrase the query when spawning agents.

### Patch discipline

PATCH, NEVER REGENERATE. After the final report exists, only surgical patch/polish edits are allowed. Patcher and polish custom agents preserve the Claude tool-lock intent in their instructions; do not claim exact Codex mechanical parity unless Codex hooks/config enforce it in this project.

### Final gates

Before declaring a run complete, run the Hyperresearch lint gates described by the active step skill, including wrapper-report, locus-coverage, scaffold-prompt, and patch-surgery where applicable.
{end_marker}
"""
```

Then add this function below `inject_agent_docs()`:

```python
def inject_codex_agent_docs(vault_root: Path) -> list[str]:
    """Inject Codex-specific hyperresearch docs into AGENTS.md at the vault root."""
    hpr_path = _resolve_executable().replace("\\", "/")
    from datetime import date

    blurb = CODEX_HYPERRESEARCH_BLURB.format(
        marker=CODEX_HYPERRESEARCH_SECTION_MARKER,
        end_marker=CODEX_HYPERRESEARCH_SECTION_END,
        hpr=hpr_path,
        today=date.today().isoformat(),
    )

    modified: list[str] = []
    result = _inject_into_file(vault_root / "AGENTS.md", blurb, "AGENTS.md")
    if result:
        modified.append(result)
    return modified
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add src/hyperresearch/core/agent_docs.py tests/test_core/test_codex_agent_docs.py
git commit -m "feat: add codex agent docs injection"
```

---

### Task 2: Codex Skill and Custom-Agent Installers

**Files:**
- Create: `src/hyperresearch/core/codex_hooks.py`
- Create: `tests/test_core/test_codex_hooks.py`

- [ ] **Step 1: Write failing Codex installer tests**

Create `tests/test_core/test_codex_hooks.py`:

```python
from __future__ import annotations

import tomllib

from hyperresearch.core.codex_hooks import (
    CODEX_AGENT_FILENAMES,
    _adapt_codex_skill_content,
    _install_codex_hyperresearch_skill,
    _install_codex_hyperresearch_step_skills,
    _install_codex_patcher_agent,
    install_codex_hooks,
    install_global_codex_hooks,
)
from hyperresearch.core.hooks import _HYPERRESEARCH_STEP_SKILLS


def test_adapt_codex_skill_content_rewrites_claude_mechanics():
    source = (
        'If `.claude/skills/hyperresearch-1-decompose/SKILL.md` is missing, '
        'run `hyperresearch install --steps-only . --json`. '
        'Then call `Skill(skill: "hyperresearch-1-decompose")`. '
        'Spawn via the Task tool with `subagent_type: hyperresearch-patcher`.'
    )

    adapted = _adapt_codex_skill_content(source)

    assert ".agents/skills/hyperresearch-1-decompose/SKILL.md" in adapted
    assert "hyperresearch install --steps-only . --codex --json" in adapted
    assert "$hyperresearch-1-decompose" in adapted
    assert "spawn the Codex custom agent `hyperresearch-patcher`" in adapted
    assert ".claude/skills" not in adapted
    assert "Skill(skill:" not in adapted
    assert "Task tool" not in adapted


def test_install_codex_entry_skill(tmp_vault):
    result = _install_codex_hyperresearch_skill(tmp_vault.root)

    assert result is not None
    skill_path = tmp_vault.root / ".agents" / "skills" / "hyperresearch" / "SKILL.md"
    assert skill_path.exists()
    body = skill_path.read_text(encoding="utf-8")
    assert "name: hyperresearch" in body
    assert ".agents/skills/hyperresearch-1-decompose/SKILL.md" in body
    assert "hyperresearch install --steps-only . --codex --json" in body
    assert "$hyperresearch-1-decompose" in body
    assert "PATCH, NEVER REGENERATE" in body
    assert ".claude/skills" not in body


def test_install_codex_step_skills_creates_all_16(tmp_vault):
    result = _install_codex_hyperresearch_step_skills(tmp_vault.root)

    assert result is not None
    skills_root = tmp_vault.root / ".agents" / "skills"
    for skill_name in _HYPERRESEARCH_STEP_SKILLS:
        skill_path = skills_root / skill_name / "SKILL.md"
        assert skill_path.exists(), f"missing Codex step skill: {skill_name}"
        body = skill_path.read_text(encoding="utf-8")
        assert f"name: {skill_name}" in body
        assert ".claude/skills" not in body
        if skill_name != "hyperresearch-16-readability-audit":
            assert "$hyperresearch-" in body


def test_install_codex_patcher_agent_uses_toml_schema(tmp_vault):
    result = _install_codex_patcher_agent(tmp_vault.root)

    assert result is not None
    agent_path = tmp_vault.root / ".codex" / "agents" / "hyperresearch-patcher.toml"
    assert agent_path.exists()
    data = tomllib.loads(agent_path.read_text(encoding="utf-8"))
    assert data["name"] == "hyperresearch-patcher"
    assert "description" in data
    assert "developer_instructions" in data
    assert data["model"] == "gpt-5.5"
    assert data["model_reasoning_effort"] == "high"
    instructions = data["developer_instructions"]
    assert "tools: Read, Edit" not in instructions
    assert "Codex custom-agent note" in instructions
    assert "PATCH" in instructions
    assert "regenerat" in instructions.lower()
    assert "research/patch-log.json" in instructions


def test_install_codex_hooks_registers_project_roster(tmp_vault):
    actions = install_codex_hooks(tmp_vault.root, "hyperresearch")

    assert actions
    assert (tmp_vault.root / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert not (tmp_vault.root / ".claude" / "settings.json").exists()
    assert not (tmp_vault.root / "CLAUDE.md").exists()
    for filename in CODEX_AGENT_FILENAMES:
        assert (tmp_vault.root / ".codex" / "agents" / filename).exists()


def test_install_codex_hooks_idempotent(tmp_vault):
    first = install_codex_hooks(tmp_vault.root, "hyperresearch")
    second = install_codex_hooks(tmp_vault.root, "hyperresearch")

    assert first
    assert second == []


def test_install_global_codex_hooks_uses_codex_user_locations(tmp_path):
    actions = install_global_codex_hooks(tmp_path, "hyperresearch")

    assert actions
    assert (tmp_path / ".codex" / "AGENTS.md").exists()
    assert (tmp_path / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "agents" / "hyperresearch-patcher.toml").exists()
    assert not (tmp_path / ".claude").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_hooks.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'hyperresearch.core.codex_hooks'`.

- [ ] **Step 3: Implement Codex installer module**

Create `src/hyperresearch/core/codex_hooks.py` with this structure:

```python
"""Codex installer for Hyperresearch skills and custom agents."""

from __future__ import annotations

import json
import re
from pathlib import Path

from hyperresearch.core.agent_docs import inject_codex_agent_docs
from hyperresearch.core.hooks import (
    CORPUS_CRITIC_AGENT,
    DEPTH_CRITIC_AGENT,
    DEPTH_INVESTIGATOR_AGENT,
    DIALECTIC_CRITIC_AGENT,
    DRAFT_ORCHESTRATOR_AGENT,
    INSTRUCTION_CRITIC_AGENT,
    LOCI_ANALYST_AGENT,
    PATCHER_AGENT,
    POLISH_AUDITOR_AGENT,
    READABILITY_REFORMATTER_AGENT,
    RESEARCHER_AGENT,
    SOURCE_ANALYST_AGENT,
    SYNTHESIZER_AGENT,
    WIDTH_CRITIC_AGENT,
    _HYPERRESEARCH_STEP_SKILLS,
    _read_skill_source,
    _render_scaffold_only_bullets,
)

CODEX_AGENT_FILENAMES: tuple[str, ...] = (
    "hyperresearch-fetcher.toml",
    "hyperresearch-loci-analyst.toml",
    "hyperresearch-depth-investigator.toml",
    "hyperresearch-source-analyst.toml",
    "hyperresearch-corpus-critic.toml",
    "hyperresearch-dialectic-critic.toml",
    "hyperresearch-depth-critic.toml",
    "hyperresearch-width-critic.toml",
    "hyperresearch-instruction-critic.toml",
    "hyperresearch-patcher.toml",
    "hyperresearch-polish-auditor.toml",
    "hyperresearch-readability-recommender.toml",
    "hyperresearch-draft-orchestrator.toml",
    "hyperresearch-synthesizer.toml",
)


def _adapt_codex_skill_content(content: str) -> str:
    """Adapt canonical Claude skill text for Codex project skill installation."""
    adapted = content.replace(".claude/skills/", ".agents/skills/")
    adapted = adapted.replace(
        "hyperresearch install --steps-only . --json",
        "hyperresearch install --steps-only . --codex --json",
    )
    adapted = re.sub(
        r'Skill\(skill: "([^"]+)"\)',
        lambda match: f"${match.group(1)}",
        adapted,
    )
    adapted = adapted.replace(
        "Task tool",
        "Codex subagent workflow",
    )
    adapted = re.sub(
        r"subagent_type: ([A-Za-z0-9_-]+)",
        lambda match: f"spawn the Codex custom agent `{match.group(1)}`",
        adapted,
    )
    adapted = adapted.replace(
        "via the Task",
        "by spawning the matching Codex custom agent",
    )
    return adapted


def _write_skill_file(root: Path, skill_name: str, content: str, label: str) -> str | None:
    skill_dir = root / ".agents" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    dest_path = skill_dir / "SKILL.md"
    if dest_path.exists() and dest_path.read_text(encoding="utf-8") == content:
        return None
    dest_path.write_text(content, encoding="utf-8")
    return f"Codex: .agents/skills/{skill_name}/SKILL.md ({label})"


def _install_codex_hyperresearch_skill(root: Path) -> str | None:
    content = _read_skill_source("hyperresearch.md")
    if content is None:
        return None
    return _write_skill_file(
        root,
        "hyperresearch",
        _adapt_codex_skill_content(content),
        "$hyperresearch entry skill",
    )


def _install_codex_hyperresearch_step_skills(root: Path) -> str | None:
    installed: list[str] = []
    for skill_name in _HYPERRESEARCH_STEP_SKILLS:
        content = _read_skill_source(f"{skill_name}.md")
        if content is None:
            continue
        result = _write_skill_file(
            root,
            skill_name,
            _adapt_codex_skill_content(content),
            "V8 step skill",
        )
        if result:
            installed.append(skill_name)
    if not installed:
        return None
    return f"Codex: .agents/skills/hyperresearch-N-*/SKILL.md ({len(installed)} step skills)"
```

Continue in the same file with agent helpers:

```python
def _extract_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    raw = content[4:end]
    body = content[end + 5 :]
    data: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in raw.splitlines():
        if line.startswith((" ", "\t")) and current_key:
            current_lines.append(line.strip())
            continue
        if current_key:
            data[current_key] = " ".join(current_lines).strip()
            current_key = None
            current_lines = []
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value == ">":
            current_key = key.strip()
            current_lines = []
        else:
            data[key.strip()] = value
    if current_key:
        data[current_key] = " ".join(current_lines).strip()
    return data, body


def _codex_model_for(claude_model: str) -> tuple[str, str]:
    if claude_model == "opus":
        return "gpt-5.5", "high"
    return "gpt-5.5", "medium"


def _adapt_agent_body_for_codex(body: str, tools: str) -> str:
    note = (
        "Codex custom-agent note: this TOML file preserves the Claude role and "
        f"tool restriction intent (`tools: {tools}`), but Codex custom agents do "
        "not document an exact Claude frontmatter tool-lock equivalent. Follow "
        "the allowed and forbidden behaviors below exactly. Do not claim exact "
        "mechanical tool-lock parity unless project Codex hooks/config enforce it.\n\n"
    )
    adapted = body.replace("Task tool", "Codex subagent workflow")
    adapted = adapted.replace("via the Task", "by spawning the matching Codex custom agent")
    adapted = re.sub(
        r"subagent_type: ([A-Za-z0-9_-]+)",
        lambda match: f"spawn the Codex custom agent `{match.group(1)}`",
        adapted,
    )
    return note + adapted


def _codex_agent_toml(content: str, hpr_path: str = "hyperresearch") -> str:
    frontmatter, body = _extract_frontmatter(content)
    name = frontmatter["name"]
    description = frontmatter.get("description", f"Hyperresearch custom agent {name}.")
    claude_model = frontmatter.get("model", "sonnet")
    tools = frontmatter.get("tools", "unspecified")
    model, reasoning = _codex_model_for(claude_model)
    instructions = _adapt_agent_body_for_codex(body, tools).replace("{hpr_path}", hpr_path)
    return "\n".join(
        [
            f"name = {json.dumps(name)}",
            f"description = {json.dumps(description)}",
            f"model = {json.dumps(model)}",
            f"model_reasoning_effort = {json.dumps(reasoning)}",
            f"developer_instructions = {json.dumps(instructions)}",
            "",
        ]
    )


def _write_codex_agent_file(root: Path, filename: str, content: str, label: str) -> str | None:
    agents_dir = root / ".codex" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    agent_path = agents_dir / filename
    if agent_path.exists() and agent_path.read_text(encoding="utf-8") == content:
        return None
    agent_path.write_text(content, encoding="utf-8")
    return f"Codex: .codex/agents/{filename} ({label})"
```

Add per-agent installers and aggregate installers:

```python
def _install_codex_patcher_agent(root: Path, hpr_path: str = "hyperresearch") -> str | None:
    return _write_codex_agent_file(
        root,
        "hyperresearch-patcher.toml",
        _codex_agent_toml(PATCHER_AGENT, hpr_path),
        "patcher custom agent",
    )


def _install_agent(root: Path, filename: str, content: str, label: str, hpr_path: str) -> str | None:
    return _write_codex_agent_file(root, filename, _codex_agent_toml(content, hpr_path), label)


def install_codex_hooks(root: Path, hpr_path: str = "hyperresearch") -> list[str]:
    actions: list[str] = []
    agent_specs = (
        ("hyperresearch-fetcher.toml", RESEARCHER_AGENT.format(hpr_path=hpr_path), "fetcher custom agent"),
        ("hyperresearch-loci-analyst.toml", LOCI_ANALYST_AGENT.format(hpr_path=hpr_path), "loci analyst custom agent"),
        ("hyperresearch-depth-investigator.toml", DEPTH_INVESTIGATOR_AGENT.format(hpr_path=hpr_path), "depth investigator custom agent"),
        ("hyperresearch-source-analyst.toml", SOURCE_ANALYST_AGENT.format(hpr_path=hpr_path), "source analyst custom agent"),
        ("hyperresearch-corpus-critic.toml", CORPUS_CRITIC_AGENT.replace("{hpr_path}", hpr_path), "corpus critic custom agent"),
        ("hyperresearch-dialectic-critic.toml", DIALECTIC_CRITIC_AGENT.format(hpr_path=hpr_path), "dialectic critic custom agent"),
        ("hyperresearch-depth-critic.toml", DEPTH_CRITIC_AGENT.format(hpr_path=hpr_path), "depth critic custom agent"),
        ("hyperresearch-width-critic.toml", WIDTH_CRITIC_AGENT.format(hpr_path=hpr_path), "width critic custom agent"),
        ("hyperresearch-instruction-critic.toml", INSTRUCTION_CRITIC_AGENT, "instruction critic custom agent"),
        ("hyperresearch-patcher.toml", PATCHER_AGENT, "patcher custom agent"),
        ("hyperresearch-polish-auditor.toml", POLISH_AUDITOR_AGENT.format(scaffold_only_sections=_render_scaffold_only_bullets(indent="- ")), "polish auditor custom agent"),
        ("hyperresearch-readability-recommender.toml", READABILITY_REFORMATTER_AGENT, "readability recommender custom agent"),
        ("hyperresearch-draft-orchestrator.toml", DRAFT_ORCHESTRATOR_AGENT.replace("{hpr_path}", hpr_path), "draft orchestrator custom agent"),
        ("hyperresearch-synthesizer.toml", SYNTHESIZER_AGENT, "synthesizer custom agent"),
    )
    for installer in (
        lambda: _install_codex_hyperresearch_skill(root),
        lambda: _install_codex_hyperresearch_step_skills(root),
    ):
        result = installer()
        if result:
            actions.append(result)
    for filename, content, label in agent_specs:
        result = _install_agent(root, filename, content, label, hpr_path)
        if result:
            actions.append(result)
    return actions


def install_global_codex_hooks(home: Path | None = None, hpr_path: str = "hyperresearch") -> list[str]:
    if home is None:
        home = Path.home()
    actions: list[str] = []
    doc_actions = inject_codex_agent_docs(home / ".codex")
    actions.extend(f"Codex: ~/.codex/{action}" for action in doc_actions)
    actions.extend(install_codex_hooks(home, hpr_path=hpr_path))
    return actions
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_hooks.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add src/hyperresearch/core/codex_hooks.py tests/test_core/test_codex_hooks.py
git commit -m "feat: install codex skills and agents"
```

---

### Task 3: CLI --codex Routing

**Files:**
- Modify: `src/hyperresearch/cli/install.py`
- Create: `tests/test_cli/test_install_codex.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli/test_install_codex.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyperresearch.cli import app

runner = CliRunner()


def test_install_codex_project_json(tmp_path: Path):
    target = tmp_path / "codex-vault"

    result = runner.invoke(app, ["install", str(target), "--codex", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["data"]["runtime"] == "codex"
    assert (target / "AGENTS.md").exists()
    assert (target / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert (target / ".codex" / "agents" / "hyperresearch-patcher.toml").exists()
    assert not (target / ".claude").exists()


def test_install_codex_steps_only_json(tmp_path: Path):
    target = tmp_path / "steps-only"

    result = runner.invoke(app, ["install", str(target), "--steps-only", "--codex", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["data"]["runtime"] == "codex"
    assert (target / ".agents" / "skills" / "hyperresearch-1-decompose" / "SKILL.md").exists()
    assert (target / ".agents" / "skills" / "hyperresearch-16-readability-audit" / "SKILL.md").exists()
    assert not (target / ".codex" / "agents").exists()
    assert not (target / ".claude").exists()


def test_install_default_stays_claude_json(tmp_path: Path):
    target = tmp_path / "claude-vault"

    result = runner.invoke(app, ["install", str(target), "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["ok"] is True
    assert "runtime" not in data["data"] or data["data"]["runtime"] == "claude"
    assert (target / "CLAUDE.md").exists()
    assert (target / ".claude" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".codex" / "agents").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cli\test_install_codex.py -q
```

Expected: FAIL because `--codex` is not a recognized option.

- [ ] **Step 3: Implement CLI routing**

In `src/hyperresearch/cli/install.py`, add the `codex` option to the function signature after `steps_only`:

```python
    codex: bool = typer.Option(
        False,
        "--codex",
        help="Install Codex project/global/step assets instead of the default Claude Code assets.",
    ),
```

Update the docstring:

```python
    """Install hyperresearch agent integration for Claude Code by default or Codex with --codex."""
```

Replace the current steps-only branch with runtime-aware routing:

```python
    if steps_only:
        target = Path(path).resolve()
        if codex:
            from hyperresearch.core.codex_hooks import _install_codex_hyperresearch_step_skills

            result = _install_codex_hyperresearch_step_skills(target)
            if json_output:
                output(
                    success(
                        {"runtime": "codex", "steps_installed": result, "target": str(target)},
                        vault=None,
                    ),
                    json_mode=True,
                )
                return
            if result:
                console.print(f"[green]Codex step skills installed:[/] {target}/.agents/skills/")
                console.print(f"  {result}")
            else:
                console.print(f"[dim]Codex step skills already installed at {target}/.agents/skills/[/]")
            return

        result = _install_hyperresearch_step_skills(target)
```

Replace the global branch with runtime-aware routing:

```python
    if global_install:
        from hyperresearch.core.agent_docs import _resolve_executable

        hpr_path = _resolve_executable()
        home = Path.home()
        if codex:
            from hyperresearch.core.codex_hooks import install_global_codex_hooks

            hook_actions = install_global_codex_hooks(home, hpr_path=hpr_path)
            if json_output:
                output(
                    success(
                        {
                            "runtime": "codex",
                            "global": True,
                            "home": str(home),
                            "hooks_installed": hook_actions,
                        },
                        vault=None,
                    ),
                    json_mode=True,
                )
                return
            console.print(f"[green]Codex global install:[/] {home}/.codex/ and {home}/.agents/")
            for action in hook_actions:
                console.print(f"  {action}")
            console.print("\n[bold]Ready.[/] $hyperresearch is now available to Codex.")
            return

        hook_actions = install_global_hooks(home, hpr_path=hpr_path)
```

In the project install path, split docs/hooks by runtime after `hpr_path = _resolve_executable()`:

```python
    if codex:
        from hyperresearch.core.agent_docs import inject_codex_agent_docs
        from hyperresearch.core.codex_hooks import install_codex_hooks

        doc_actions = inject_codex_agent_docs(root)
        hook_actions = install_codex_hooks(root, hpr_path=hpr_path)
    else:
        from hyperresearch.core.agent_docs import inject_agent_docs

        doc_actions = inject_agent_docs(root)
        hook_actions = install_hooks(root, hpr_path=hpr_path)
```

Add `"runtime": "codex" if codex else "claude"` to the JSON `data` dict.

Update human output labels so Codex project installs print `Codex files installed` or equivalent and mention `.agents/skills/` plus `.codex/agents/`.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cli\test_install_codex.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add src/hyperresearch/cli/install.py tests/test_cli/test_install_codex.py
git commit -m "feat: route install codex option"
```

---

### Task 4: Integration Verification and Regression Coverage

**Files:**
- Modify: `tests/test_core/test_hooks.py` only if a Claude regression appears and a test needs a clearer assertion.
- Modify: `tests/test_core/test_codex_hooks.py` only if integration reveals a missing invariant assertion.

- [ ] **Step 1: Run narrow installer tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_core\test_hooks.py tests\test_core\test_codex_agent_docs.py tests\test_core\test_codex_hooks.py tests\test_cli\test_install_codex.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full pytest suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run lint**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
```

Expected: PASS.

- [ ] **Step 4: Run CLI smoke**

Run:

```powershell
.\.venv\Scripts\python.exe -m hyperresearch --help
```

Expected: exits 0 and the install help still lists the `install` command.

- [ ] **Step 5: Run mypy and record baseline status**

Run:

```powershell
.\.venv\Scripts\python.exe -m mypy src
```

Expected: FAIL with the pre-existing strict-typing errors noted in this plan unless earlier unrelated work fixed them. Do not broaden this feature branch to fix unrelated mypy debt. If new errors mention `codex_hooks.py`, `agent_docs.py`, or `install.py`, fix those new errors.

- [ ] **Step 6: Review generated files in a temp install**

Run:

```powershell
$tmp = New-Item -ItemType Directory -Path ([System.IO.Path]::Combine($env:TEMP, "hpr-codex-install-" + [System.Guid]::NewGuid().ToString("N")))
.\.venv\Scripts\python.exe -m hyperresearch install $tmp.FullName --codex --json
Get-ChildItem -Recurse $tmp.FullName\.agents, $tmp.FullName\.codex | Select-Object FullName
```

Expected: output includes `.agents/skills/hyperresearch/SKILL.md`, all 16 `.agents/skills/hyperresearch-N-*/SKILL.md` files, and `.codex/agents/hyperresearch-patcher.toml`. It must not include `.claude`.

- [ ] **Step 7: Commit verification-only test adjustments if any**

If Step 1 through Step 6 required test-only assertion fixes, commit them:

```powershell
git add tests
git commit -m "test: cover codex install integration"
```

If no files changed, do not create an empty commit.

---

## Final Handoff

After all tasks pass review under `subagent-driven-development`, use `superpowers:finishing-a-development-branch`. Final verification should report:

- Worktree path: `E:\Deep Research\hyperresearch\.worktrees\codex-v8-support`
- Branch: `codex/codex-v8-support`
- Passing checks: narrow installer tests, full pytest, ruff, CLI smoke.
- Known baseline limitation: `mypy src` fails with pre-existing unrelated errors unless fixed outside this plan.
