# Codex Agent Doc Template Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate Claude `CLAUDE.md` and Codex `AGENTS.md` from one canonical markdown template while preserving the full current Claude guidance and adding explicit Codex doc-refresh flags.

**Architecture:** Move the full current `HYPERRESEARCH_BLURB` body into `src/hyperresearch/templates/agent_docs/hyperresearch_project.md` with named runtime placeholders. `src/hyperresearch/core/agent_docs.py` becomes a renderer/injector: it loads the template with `importlib.resources`, fills a Claude or Codex runtime context, and injects the rendered section into the correct project doc. CLI refresh commands gain explicit `--claude` / `--codex` options.

**Tech Stack:** Python 3.11, Typer, importlib.resources, pytest, ruff.

---

## File Structure

- Create `src/hyperresearch/templates/__init__.py`: package marker for bundled templates.
- Create `src/hyperresearch/templates/agent_docs/__init__.py`: package marker for agent-doc templates.
- Create `src/hyperresearch/templates/agent_docs/hyperresearch_project.md`: canonical project-doc markdown template, starting from the full current `HYPERRESEARCH_BLURB` body.
- Modify `src/hyperresearch/core/agent_docs.py`: replace independent long strings with template loading, runtime rendering, and existing injection behavior.
- Modify `src/hyperresearch/cli/config_cmd.py`: add `--claude` / `--codex` options to `config agent-docs`.
- Modify `src/hyperresearch/cli/repair.py`: add `--claude` / `--codex` options to `repair --docs`.
- Modify `tests/test_core/test_codex_agent_docs.py`: add renderer parity and Codex leakage tests.
- Modify `tests/test_cli/test_install_codex.py`: assert installed Codex docs contain full operational sections.
- Create `tests/test_cli/test_agent_docs_runtime_flags.py`: test explicit refresh flags for config and repair.

Do not modify `src/hyperresearch/skills/*.md`, benchmark text, README claims, or Codex custom-agent TOML generation unless a failing test proves a direct need.

---

### Task 1: Write Failing Renderer and Codex Parity Tests

**Files:**
- Modify: `tests/test_core/test_codex_agent_docs.py`

- [ ] **Step 1: Add imports for the new renderer**

Update the import block to include `render_agent_docs`:

```python
from hyperresearch.core.agent_docs import (
    CODEX_HYPERRESEARCH_SECTION_END,
    CODEX_HYPERRESEARCH_SECTION_MARKER,
    HYPERRESEARCH_SECTION_END,
    HYPERRESEARCH_SECTION_MARKER,
    inject_codex_agent_docs,
    render_agent_docs,
)
```

- [ ] **Step 2: Add a deterministic section-heading parity test**

Add this test after the imports:

```python
def _section_headings(body: str) -> list[str]:
    return [
        line.strip()
        for line in body.splitlines()
        if line.startswith("### ")
    ]


def test_render_agent_docs_keeps_claude_and_codex_sections_in_parity():
    claude = render_agent_docs("claude", hpr_path="C:/Tools/hyperresearch.exe", today="2026-06-07")
    codex = render_agent_docs("codex", hpr_path="C:/Tools/hyperresearch.exe", today="2026-06-07")

    assert _section_headings(claude) == _section_headings(codex)
    assert _section_headings(claude) == [
        "### How to do research",
        "### What the skill files own",
        "### Canonical research query",
        "### Academic APIs before web search",
        "### PDFs fetch directly",
        "### Searching the vault",
        "### Images, screenshots, and assets",
        "### Authenticated crawling",
        "### Curate after every session",
        "### Key conventions",
    ]
```

- [ ] **Step 3: Add required invariant tests for both runtimes**

Add:

```python
def test_render_agent_docs_preserves_load_bearing_guidance_for_both_runtimes():
    required = (
        "Paths in this document are relative to your current working directory",
        "Do NOT use WebFetch for source pages",
        "The skill files own everything about how to research",
        "research/query-<vault_tag>.md",
        "Academic APIs before web search",
        "Semantic Scholar",
        "PDFs fetch directly",
        "Searching the vault",
        "Images, screenshots, and assets",
        "Authenticated crawling",
        "Curate after every session",
        "note list --status draft",
        "Summaries must be specific",
        "Notes live in `research/notes/`",
        "Run `{hpr} --help` for the full command list",
    )

    for runtime in ("claude", "codex"):
        body = render_agent_docs(runtime, hpr_path="{hpr}", today="2026-06-07")
        for expected in required:
            assert expected in body
```

- [ ] **Step 4: Add runtime-specific mechanics tests**

Add:

```python
def test_render_agent_docs_uses_runtime_specific_mechanics():
    claude = render_agent_docs("claude", hpr_path="hyperresearch", today="2026-06-07")
    codex = render_agent_docs("codex", hpr_path="hyperresearch", today="2026-06-07")

    assert HYPERRESEARCH_SECTION_MARKER in claude
    assert HYPERRESEARCH_SECTION_END in claude
    assert "/hyperresearch <query>" in claude
    assert ".claude/skills/hyperresearch/SKILL.md" in claude
    assert 'Skill(skill: "hyperresearch-N-...")' in claude
    assert "Task call" in claude

    assert CODEX_HYPERRESEARCH_SECTION_MARKER in codex
    assert CODEX_HYPERRESEARCH_SECTION_END in codex
    assert "$hyperresearch <query>" in codex
    assert ".agents/skills/hyperresearch/SKILL.md" in codex
    assert ".codex/agents/" in codex
    assert "Codex custom-agent spawn" in codex

    assert ".claude/skills" not in codex
    assert "/hyperresearch <query>" not in codex
    assert "Task call" not in codex
    assert "Task calls" not in codex
    assert "Task tool" not in codex
```

- [ ] **Step 5: Strengthen the existing Codex injection test**

In `test_inject_codex_agent_docs_creates_agents_md`, add these assertions before `assert not (tmp_path / "CLAUDE.md").exists()`:

```python
    assert "Do NOT use WebFetch for source pages" in body
    assert "Academic APIs before web search" in body
    assert "Curate after every session" in body
    assert ".claude/skills" not in body
    assert "/hyperresearch <query>" not in body
    assert "Task call" not in body
```

- [ ] **Step 6: Run the new renderer tests and verify they fail**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py -q
```

Expected: FAIL with `ImportError` for `render_agent_docs` or assertion failures from the current thin Codex blurb.

- [ ] **Step 7: Commit the failing tests**

```powershell
git add tests/test_core/test_codex_agent_docs.py
git commit -m "test: require agent doc template parity"
```

---

### Task 2: Add Canonical Template and Renderer

**Files:**
- Create: `src/hyperresearch/templates/__init__.py`
- Create: `src/hyperresearch/templates/agent_docs/__init__.py`
- Create: `src/hyperresearch/templates/agent_docs/hyperresearch_project.md`
- Modify: `src/hyperresearch/core/agent_docs.py`

- [ ] **Step 1: Create package marker files**

Create empty package marker files:

```python
# src/hyperresearch/templates/__init__.py
"""Bundled templates for hyperresearch."""
```

```python
# src/hyperresearch/templates/agent_docs/__init__.py
"""Bundled agent project-document templates."""
```

- [ ] **Step 2: Create the canonical markdown template**

Create `src/hyperresearch/templates/agent_docs/hyperresearch_project.md` by moving the full current `HYPERRESEARCH_BLURB` body from `agent_docs.py` into the file, then replacing only runtime-specific text with placeholders.

The template must include this exact structure and all current sections:

```md
{marker}
## {heading}

**CLI path: `{hpr}`** — use this exact path for every hyperresearch command. It may not be on your system PATH.

**Paths in this document are relative to your current working directory**, not to the CLI binary's location. Use `research/notes/final_report_<vault_tag>.md` (not a prefix with the binary path) when you save files.

This project uses hyperresearch as an agent-driven research knowledge base. The `research/` directory contains markdown notes collected from web sources and original research. Append `--json` to any command for structured output.

{runtime_trust_note}

### How to do research

**Run a research session with `{research_entrypoint}`.** This invokes the V8 16-step pipeline. The entry skill at `{entry_skill_path}` is a thin ROUTER. The 16 step procedures live in their own skills (`hyperresearch-1-decompose` through `hyperresearch-16-readability-audit`) and are loaded fresh into context via {step_loading_mechanic} when each step runs. This solves V7's context-compaction problem: each step's procedure lands in context only when needed. Read the entry skill before you start a research session; it explains the chain mechanics.

If step skills are missing, run `{install_steps_command}`. This installs the 16 step skill files needed by the runtime-specific step invocation mechanics.

Step 1 classifies the query into one of two tiers (`light` or `full`) and the rest of the pipeline scales accordingly — short bounded queries skip the depth investigations, critics, and patcher (~30-40 min); argumentative deep-research queries run all 16 steps with adversarial review (~1.5-2.5 hours).

**Do NOT use WebFetch for source pages** — use `{hpr} fetch` instead. The skill files explain when to fetch vs. search.

### What the skill files own

The skill files own everything about how to research. That includes:
- The pipeline phases and what each phase does
- Which subagents exist and what each one is for ({subagent_roster})
- The tool-lock invariant (patcher and polish-auditor can only Read + Edit, never Write)
- The subagent spawn contract (every {subagent_call_label} passes the verbatim research_query + pipeline position + inputs)
- Artifact locations (`research/scaffold.md`, `research/prompt-decomposition.json`, `research/loci.json`, `research/comparisons.md`, interim notes, patch / polish logs)
- The curation pass after every research session

If you need to know how hyperresearch works, read the skill file. This document does NOT duplicate that content — when the skill file and this file disagree, the skill file wins.

### Canonical research query

In a normal run, the canonical research query is the user's verbatim prompt. In wrapped runs, if `research/prompt.txt` exists, that file is gospel and overrides any wrapping instructions. The pipeline persists the query as `research/query-<vault_tag>.md` with YAML frontmatter — this is the canonical query reference for all downstream layers. Wrapper requirements (save path, citation format, terminal sections) are a separate contract, captured in the scaffold — not pasted into the `## User Prompt (VERBATIM — gospel)` section.

### Academic APIs before web search

For any topic with a research literature, hit academic APIs BEFORE running web searches. They return citation-ranked canonical papers; web search returns derivative commentary.

- **Semantic Scholar:** `https://api.semanticscholar.org/graph/v1/paper/search?query=<q>&fields=title,year,citationCount,externalIds&limit=10` — then citation-chain the top papers forward + backward.
- **arXiv:** `https://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+all:<q>&sortBy=relevance&max_results=25`
- **OpenAlex:** `https://api.openalex.org/works?search=<q>&sort=cited_by_count:desc&per-page=15&mailto=research@example.com`
- **PubMed:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<q>&retmode=json&retmax=20`

After the academic sweep, run web searches for context, news, non-academic angles, and at least one adversarial search ("criticism of X", "limitations of X").

### PDFs fetch directly

`{hpr} fetch` auto-detects PDF URLs (arXiv, NBER, SSRN, direct `.pdf` links) and extracts full text via pymupdf. Fetch them aggressively. Raw PDFs land in `research/raw/<note-id>.pdf` and the note's frontmatter links back via `raw_file:`.

### Searching the vault

```bash
{hpr} search "query" --json                # Full-text search
{hpr} search "query" --tag ml --json       # Filter by tag / status / date / parent
{hpr} search "query" --include-body --json # Full-body search, not just titles
{hpr} note show <id> --json                # Read one note
{hpr} note show <id1> <id2> <id3> --json   # Batch-read notes in one call
{hpr} note list --json                     # List all notes with summaries
{hpr} tags --json                          # Existing tag vocabulary
```

### Images, screenshots, and assets

```bash
{hpr} fetch "<url>" --tag <topic> --save-assets -j   # Saves screenshot + top images
{hpr} assets list --note <note-id> --json            # Assets for a specific note
{hpr} assets path <note-id> --type screenshot -j     # Get screenshot path (viewable with Read)
```

### Authenticated crawling

Login-gated content (LinkedIn, Twitter, paywalled news) needs a browser profile. Set up once via `{hpr} setup` or `crwl profiles`. Config in `.hyperresearch/config.toml` under `[web]`: `profile = "research"`, `magic = true`. LinkedIn / Twitter / Facebook / Instagram / TikTok auto-use a visible browser to avoid session kills.

If a fetch returns a login wall, tell the user to run `{hpr} setup` and create a login profile.

### Curate after every session

Every research session must end with a curation pass:

```bash
{hpr} note list --status draft -j                                        # Find unprocessed notes
{hpr} note show <id> -j                                                  # Read the content
{hpr} note update <id> --summary "<specific summary>" --add-tag <t> -j   # Add summary + tags
{hpr} lint -j                                                            # Find missing tags / summaries / broken links
{hpr} repair -j                                                          # Auto-fix broken links, rebuild indexes
{hpr} status -j                                                          # Overall vault health
```

Lifecycle: `draft` → `review` → `evergreen` (or `stale` → `deprecated` → `archive` for outdated material).

Summaries must be specific — "Mamba achieves linear-time sequence modeling via selective state spaces" beats "Paper about Mamba". Reuse the existing tag vocabulary (`{hpr} tags -j`) rather than inventing new tags.

### Key conventions

- Notes live in `research/notes/` as markdown with YAML frontmatter
- Link notes with `[[note-id]]` syntax
- After editing `.md` files directly, run `{hpr} sync` to update the index
- Markdown is truth and SQLite is cache; do not make the database authoritative for note content
- After `research/notes/final_report_<vault_tag>.md` exists, PATCH, NEVER REGENERATE. Patcher and polish agents may revise by targeted edits only and must not overwrite or regenerate the report wholesale.
- Run `{hpr} --help` for the full command list
{end_marker}
```

- [ ] **Step 3: Replace string constants with a renderer**

In `src/hyperresearch/core/agent_docs.py`, remove `HYPERRESEARCH_BLURB` and `CODEX_HYPERRESEARCH_BLURB` and add:

```python
from typing import Literal

AgentDocsRuntime = Literal["claude", "codex"]


def _read_project_doc_template() -> str:
    """Read the bundled project-doc template."""
    import importlib.resources

    try:
        return (
            importlib.resources.files("hyperresearch.templates.agent_docs")
            .joinpath("hyperresearch_project.md")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError):
        template_path = (
            Path(__file__).parent.parent
            / "templates"
            / "agent_docs"
            / "hyperresearch_project.md"
        )
        return template_path.read_text(encoding="utf-8")
```

Then add:

```python
def _runtime_context(runtime: AgentDocsRuntime, hpr_path: str, today: str | None) -> dict[str, str]:
    hpr = hpr_path.replace("\\", "/")
    if runtime == "claude":
        return {
            "marker": HYPERRESEARCH_SECTION_MARKER,
            "end_marker": HYPERRESEARCH_SECTION_END,
            "heading": f"Research Base (hyperresearch) — Today is {today}",
            "hpr": hpr,
            "runtime_trust_note": "",
            "research_entrypoint": "/hyperresearch <query>",
            "entry_skill_path": ".claude/skills/hyperresearch/SKILL.md",
            "step_loading_mechanic": '`Skill(skill: "hyperresearch-N-...")` calls',
            "install_steps_command": f"{hpr} install --steps-only . --json",
            "subagent_roster": "fetcher, loci-analyst, depth-investigator, 4 critics, patcher, polish-auditor",
            "subagent_call_label": "Task call",
        }
    if runtime == "codex":
        return {
            "marker": CODEX_HYPERRESEARCH_SECTION_MARKER,
            "end_marker": CODEX_HYPERRESEARCH_SECTION_END,
            "heading": "Hyperresearch Codex Project Instructions",
            "hpr": hpr,
            "runtime_trust_note": (
                "This repository is trusted for Codex project configuration under `.codex/`. "
                "Codex support is additive to Claude Code support and uses the same V8 source material."
            ),
            "research_entrypoint": "$hyperresearch <query>",
            "entry_skill_path": ".agents/skills/hyperresearch/SKILL.md",
            "step_loading_mechanic": "Codex skill invocation / progressive disclosure",
            "install_steps_command": f"{hpr} install --steps-only . --codex --json",
            "subagent_roster": (
                "fetcher, loci-analyst, depth-investigator, source-analyst, corpus/dialectic/depth/"
                "width/instruction critics, patcher, polish-auditor, readability recommender, "
                "draft-orchestrator, synthesizer"
            ),
            "subagent_call_label": "Codex custom-agent spawn",
        }
    raise ValueError(f"Unknown agent docs runtime: {runtime}")
```

Then add:

```python
def render_agent_docs(
    runtime: AgentDocsRuntime,
    hpr_path: str = "hyperresearch",
    today: str | None = None,
) -> str:
    """Render Hyperresearch project instructions for one agent runtime."""
    if today is None:
        from datetime import date

        today = date.today().isoformat()
    template = _read_project_doc_template()
    return template.format(**_runtime_context(runtime, hpr_path, today)).strip()
```

- [ ] **Step 4: Update injectors to use the renderer**

Update `inject_agent_docs`:

```python
def inject_agent_docs(vault_root: Path) -> list[str]:
    """Inject Claude Code hyperresearch docs into CLAUDE.md at the vault root."""
    blurb = render_agent_docs("claude", hpr_path=_resolve_executable())

    modified: list[str] = []
    result = _inject_into_file(vault_root / "CLAUDE.md", blurb, "CLAUDE.md")
    if result:
        modified.append(result)
    return modified
```

Update `inject_codex_agent_docs`:

```python
def inject_codex_agent_docs(vault_root: Path) -> list[str]:
    """Inject Codex hyperresearch docs into AGENTS.md at the vault root."""
    blurb = render_agent_docs("codex", hpr_path=_resolve_executable())

    modified: list[str] = []
    result = _inject_into_file(vault_root / "AGENTS.md", blurb, "AGENTS.md")
    if result:
        modified.append(result)
    return modified
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py tests\test_core\test_vault.py -q
```

Expected: tests pass.

- [ ] **Step 6: Run ruff**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m ruff check src tests
```

Expected: `All checks passed!`

- [ ] **Step 7: Commit template and renderer**

```powershell
git add src/hyperresearch/templates src/hyperresearch/core/agent_docs.py tests/test_core/test_codex_agent_docs.py
git commit -m "fix: render agent docs from shared template"
```

---

### Task 3: Add Explicit Runtime Flags for `config agent-docs`

**Files:**
- Create: `tests/test_cli/test_agent_docs_runtime_flags.py`
- Modify: `src/hyperresearch/cli/config_cmd.py`

- [ ] **Step 1: Add failing CLI tests for `config agent-docs --codex` and default Claude behavior**

Create `tests/test_cli/test_agent_docs_runtime_flags.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyperresearch.cli import app

runner = CliRunner()


def _json_data(result):
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    return payload["data"]


def test_config_agent_docs_defaults_to_claude(tmp_path: Path, monkeypatch):
    result = runner.invoke(app, ["install", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    (tmp_path / "CLAUDE.md").unlink()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "agent-docs", "--json"])

    data = _json_data(result)
    assert data["runtime"] == "claude"
    assert (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / "AGENTS.md").exists()


def test_config_agent_docs_codex_updates_agents_md(tmp_path: Path, monkeypatch):
    result = runner.invoke(app, ["install", str(tmp_path), "--codex", "--json"])
    assert result.exit_code == 0, result.output
    (tmp_path / "AGENTS.md").unlink()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["config", "agent-docs", "--codex", "--json"],
    )

    data = _json_data(result)
    assert data["runtime"] == "codex"
    assert (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / "CLAUDE.md").exists()
    body = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Academic APIs before web search" in body
    assert ".claude/skills" not in body


def test_config_agent_docs_rejects_both_runtime_flags(tmp_path: Path, monkeypatch):
    result = runner.invoke(app, ["install", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["config", "agent-docs", "--claude", "--codex", "--json"],
    )

    assert result.exit_code != 0
    assert "Choose only one runtime" in result.output
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_cli\test_agent_docs_runtime_flags.py -q
```

Expected: FAIL because `--codex` / `--claude` do not exist.

- [ ] **Step 3: Implement runtime flags in `config_agent_docs`**

In `src/hyperresearch/cli/config_cmd.py`, update `config_agent_docs` signature:

```python
def config_agent_docs(
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
    claude: bool = typer.Option(False, "--claude", help="Update Claude Code CLAUDE.md."),
    codex: bool = typer.Option(False, "--codex", help="Update Codex AGENTS.md."),
) -> None:
```

Then replace the body with:

```python
    if claude and codex:
        console.print("[red]Choose only one runtime: --claude or --codex.[/]")
        raise typer.Exit(1)

    runtime = "codex" if codex else "claude"
    from hyperresearch.core.vault import Vault

    vault = Vault.discover()
    if runtime == "codex":
        from hyperresearch.core.agent_docs import inject_codex_agent_docs

        modified = inject_codex_agent_docs(vault.root)
        target = "AGENTS.md"
    else:
        from hyperresearch.core.agent_docs import inject_agent_docs

        modified = inject_agent_docs(vault.root)
        target = "CLAUDE.md"

    if json_output:
        output(
            success({"modified": modified, "runtime": runtime}, vault=str(vault.root)),
            json_mode=True,
        )
    else:
        if modified:
            for m in modified:
                console.print(f"  [green]{m}[/]")
        else:
            console.print(f"[dim]{target} already up to date.[/]")
```

The explicit `--claude` flag is accepted but does not change default behavior.

- [ ] **Step 4: Run runtime flag tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_cli\test_agent_docs_runtime_flags.py -q
```

Expected: tests pass.

- [ ] **Step 5: Commit config runtime flags**

```powershell
git add src/hyperresearch/cli/config_cmd.py tests/test_cli/test_agent_docs_runtime_flags.py
git commit -m "feat: add runtime flags for agent docs refresh"
```

---

### Task 4: Add Explicit Runtime Flags for `repair --docs`

**Files:**
- Modify: `src/hyperresearch/cli/repair.py`
- Modify: `tests/test_cli/test_agent_docs_runtime_flags.py`

- [ ] **Step 1: Add failing repair runtime tests**

Append to `tests/test_cli/test_agent_docs_runtime_flags.py`:

```python
def test_repair_docs_defaults_to_claude(tmp_path: Path, monkeypatch):
    result = runner.invoke(app, ["install", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    (tmp_path / "CLAUDE.md").unlink()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["repair", "--no-stub", "--no-enrich", "--no-promote", "--no-index", "--json"],
    )

    data = _json_data(result)
    assert data["agent_docs_runtime"] == "claude"
    assert (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / "AGENTS.md").exists()


def test_repair_docs_codex_updates_agents_md(tmp_path: Path, monkeypatch):
    result = runner.invoke(app, ["install", str(tmp_path), "--codex", "--json"])
    assert result.exit_code == 0, result.output
    (tmp_path / "AGENTS.md").unlink()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "repair",
            "--no-stub",
            "--no-enrich",
            "--no-promote",
            "--no-index",
            "--codex",
            "--json",
        ],
    )

    data = _json_data(result)
    assert data["agent_docs_runtime"] == "codex"
    assert (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / "CLAUDE.md").exists()


def test_repair_docs_rejects_both_runtime_flags(tmp_path: Path, monkeypatch):
    result = runner.invoke(app, ["install", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "repair",
            "--no-stub",
            "--no-enrich",
            "--no-promote",
            "--no-index",
            "--claude",
            "--codex",
            "--json",
        ],
    )

    assert result.exit_code != 0
    assert "Choose only one runtime" in result.output
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_cli\test_agent_docs_runtime_flags.py -q
```

Expected: FAIL because `repair` does not accept `--codex` / `--claude`.

- [ ] **Step 3: Implement runtime flags in `repair`**

Update `repair` signature in `src/hyperresearch/cli/repair.py`:

```python
    update_docs: bool = typer.Option(True, "--docs/--no-docs", help="Update runtime agent docs"),
    claude: bool = typer.Option(False, "--claude", help="Update Claude Code CLAUDE.md when --docs is enabled."),
    codex: bool = typer.Option(False, "--codex", help="Update Codex AGENTS.md when --docs is enabled."),
```

After vault discovery, add:

```python
    if claude and codex:
        console.print("[red]Choose only one runtime: --claude or --codex.[/]")
        raise typer.Exit(1)
    docs_runtime = "codex" if codex else "claude"
```

In the `if update_docs:` block, replace the Claude-only injection with:

```python
        if docs_runtime == "codex":
            from hyperresearch.core.agent_docs import inject_codex_agent_docs

            modified = inject_codex_agent_docs(vault.root)
        else:
            from hyperresearch.core.agent_docs import inject_agent_docs

            modified = inject_agent_docs(vault.root)
        report["agent_docs"] = modified
        report["agent_docs_runtime"] = docs_runtime
```

In the `else` branch for `--no-docs`, set:

```python
        report["agent_docs_runtime"] = None
```

- [ ] **Step 4: Run runtime flag tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_cli\test_agent_docs_runtime_flags.py -q
```

Expected: tests pass.

- [ ] **Step 5: Commit repair runtime flags**

```powershell
git add src/hyperresearch/cli/repair.py tests/test_cli/test_agent_docs_runtime_flags.py
git commit -m "feat: add runtime flags for repair docs"
```

---

### Task 5: Strengthen Install-Level Tests and Run Full Verification

**Files:**
- Modify: `tests/test_cli/test_install_codex.py`

- [ ] **Step 1: Add installed Codex doc content assertions**

In `test_install_codex_json_creates_vault_and_codex_assets`, after `assert (target / "AGENTS.md").exists()`, add:

```python
    agents_body = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "Do NOT use WebFetch for source pages" in agents_body
    assert "Academic APIs before web search" in agents_body
    assert "Curate after every session" in agents_body
    assert ".agents/skills/hyperresearch/SKILL.md" in agents_body
    assert ".claude/skills" not in agents_body
    assert "/hyperresearch <query>" not in agents_body
    assert "Task call" not in agents_body
```

- [ ] **Step 2: Run install tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_cli\test_install_codex.py -q
```

Expected: tests pass.

- [ ] **Step 3: Run focused surface tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py tests\test_core\test_codex_hooks.py tests\test_cli\test_install_codex.py tests\test_cli\test_agent_docs_runtime_flags.py tests\test_core\test_hooks.py tests\test_core\test_vault.py -q
```

Expected: all focused tests pass.

- [ ] **Step 4: Run full pytest**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest -q
```

Expected: full test suite passes.

- [ ] **Step 5: Run ruff**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m ruff check src tests
```

Expected: `All checks passed!`

- [ ] **Step 6: Generate sample docs for advisory review**

Run:

```powershell
$tmp = New-Item -ItemType Directory -Force -Path "$env:TEMP\hpr-agent-doc-template-parity"
..\..\.venv\Scripts\python.exe -m hyperresearch install "$($tmp.FullName)\claude" --json
..\..\.venv\Scripts\python.exe -m hyperresearch install "$($tmp.FullName)\codex" --codex --json
```

Expected files:

```text
$env:TEMP\hpr-agent-doc-template-parity\claude\CLAUDE.md
$env:TEMP\hpr-agent-doc-template-parity\codex\AGENTS.md
```

- [ ] **Step 7: Spawn a Codex review subagent for semantic equivalence**

Use a read-only review subagent with GPT-5.4-mini medium reasoning. Give it both generated files and ask:

```text
Review these generated Hyperresearch project instruction files:
- CLAUDE.md
- AGENTS.md

Judge whether they are semantically equivalent except for runtime-specific mechanics.
Runtime-specific differences that are allowed: file names, markers, Claude slash command vs Codex skill invocation, .claude/skills vs .agents/skills, Claude Task mechanics vs Codex custom-agent spawns, Codex trust/config note.

Report:
1. Missing load-bearing guidance in either file.
2. Any runtime leakage, such as Claude-only mechanics in AGENTS.md.
3. Any wording that would weaken Codex behavior versus Claude.
4. A final PASS/FAIL recommendation.
```

Expected: reviewer returns PASS or only non-blocking observations. If it returns blocking findings, fix them before completion.

- [ ] **Step 8: Commit install test**

```powershell
git add tests/test_cli/test_install_codex.py
git commit -m "test: assert installed codex docs preserve guidance"
```

- [ ] **Step 9: Check final git status**

Run:

```powershell
git status --short
```

Expected: clean working tree after all commits.
