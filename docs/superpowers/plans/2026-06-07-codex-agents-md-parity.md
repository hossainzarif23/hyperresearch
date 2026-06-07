# Codex AGENTS.md Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated Codex `AGENTS.md` files Codex-native equivalents of Claude Code `CLAUDE.md` project instructions.

**Architecture:** Replace the separate thin Codex blurb with a shared runtime-guidance renderer in `src/hyperresearch/core/agent_docs.py`. The renderer will keep common guidance sections in one place and substitute Claude-specific or Codex-specific entrypoints, skill paths, subagent wording, and markers.

**Tech Stack:** Python 3.11, Typer CLI tests, pytest, ruff.

---

## File Structure

- Modify `src/hyperresearch/core/agent_docs.py`: introduce a small `_render_hyperresearch_blurb(...)` helper and rebuild `HYPERRESEARCH_BLURB` / `CODEX_HYPERRESEARCH_BLURB` from shared source material.
- Modify `tests/test_core/test_codex_agent_docs.py`: add load-bearing parity assertions for the generated Codex `AGENTS.md`.
- Optionally modify `tests/test_cli/test_install_codex.py`: add one install-level assertion that installed `AGENTS.md` includes a representative deep guidance section.

Do not modify `src/hyperresearch/skills/*.md`, `src/hyperresearch/core/codex_hooks.py`, README benchmark text, or Claude hook templates unless a failing test proves a direct need.

---

### Task 1: Add Failing Codex AGENTS.md Parity Tests

**Files:**
- Modify: `tests/test_core/test_codex_agent_docs.py`

- [ ] **Step 1: Add section-level expectations**

In `test_inject_codex_agent_docs_creates_agents_md`, after the existing assertions for CLI path and before `assert not (tmp_path / "CLAUDE.md").exists()`, add:

```python
    required_codex_guidance = (
        "Paths in this document are relative to your current working directory",
        "Run a research session with `$hyperresearch <query>`",
        ".agents/skills/hyperresearch/SKILL.md",
        "hyperresearch-1-decompose",
        "hyperresearch-16-readability-audit",
        "loaded fresh into context",
        "Do NOT use WebFetch for source pages",
        "What the skill files own",
        "Codex custom-agent spawn contract",
        "Academic APIs before web search",
        "Semantic Scholar",
        "PDFs fetch directly",
        "Searching the vault",
        "Images, screenshots, and assets",
        "Authenticated crawling",
        "Curate after every session",
        "note list --status draft",
        "Notes live in `research/notes/`",
    )
    for expected in required_codex_guidance:
        assert expected in body
```

- [ ] **Step 2: Add Claude leakage guards**

Still in `test_inject_codex_agent_docs_creates_agents_md`, add:

```python
    assert ".claude/skills" not in body
    assert "Task call" not in body
    assert "Task calls" not in body
    assert "Task tool" not in body
    assert "Run a research session with `/hyperresearch <query>`" not in body
```

- [ ] **Step 3: Run the focused test and verify it fails**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py::test_inject_codex_agent_docs_creates_agents_md -q
```

Expected: FAIL because the current Codex `AGENTS.md` lacks the Claude-equivalent operational sections.

- [ ] **Step 4: Commit the failing test**

```powershell
git add tests/test_core/test_codex_agent_docs.py
git commit -m "test: require codex agents md runtime guidance parity"
```

---

### Task 2: Implement Shared Runtime Guidance Renderer

**Files:**
- Modify: `src/hyperresearch/core/agent_docs.py`

- [ ] **Step 1: Replace static `HYPERRESEARCH_BLURB` and `CODEX_HYPERRESEARCH_BLURB` with a shared renderer**

In `src/hyperresearch/core/agent_docs.py`, replace the two large string constants with a helper shaped like this:

```python
def _render_hyperresearch_blurb(
    *,
    marker: str,
    end_marker: str,
    hpr: str,
    runtime_name: str,
    title: str,
    entrypoint: str,
    entry_skill_path: str,
    step_skill_root: str,
    step_loading_mechanic: str,
    subagent_mechanic: str,
    subagent_roster: str,
    install_steps_command: str,
    today: str | None = None,
) -> str:
    today_suffix = f" — Today is {today}" if today else ""
    return f"""
{marker}
## {title}{today_suffix}

**CLI path: `{hpr}`** — use this exact path for every hyperresearch command. It may not be on your system PATH.

**Paths in this document are relative to your current working directory**, not to the CLI binary's location. Use `research/notes/final_report_<vault_tag>.md` (not a prefix with the binary path) when you save files.

This project uses hyperresearch as an agent-driven research knowledge base. The `research/` directory contains markdown notes collected from web sources and original research. Append `--json` to any command for structured output.

### How to do research

**Run a research session with `{entrypoint}`.** This invokes the V8 16-step pipeline. The entry skill at `{entry_skill_path}` is a thin ROUTER. The 16 step procedures live in their own skills (`hyperresearch-1-decompose` through `hyperresearch-16-readability-audit`) and are loaded fresh into context {step_loading_mechanic}. This solves V7's context-compaction problem: each step's procedure lands in context only when needed. Read the entry skill before you start a research session; it explains the chain mechanics.

If the step skills are missing, run `{install_steps_command}` to provision them under `{step_skill_root}`.

Step 1 classifies the query into one of two tiers (`light` or `full`) and the rest of the pipeline scales accordingly — short bounded queries skip the depth investigations, critics, and patcher (~30-40 min); argumentative deep-research queries run all 16 steps with adversarial review (~1.5-2.5 hours).

**Do NOT use WebFetch for source pages** — use `{hpr} fetch` instead. The skill files explain when to fetch vs. search.

### What the skill files own

The skill files own everything about how to research. That includes:
- The pipeline phases and what each phase does
- Which subagents exist and what each one is for ({subagent_roster})
- The tool-lock invariant (patcher and polish-auditor can only Read + Edit, never Write)
- The {subagent_mechanic} spawn contract (every delegated agent receives the verbatim research_query + pipeline position + inputs)
- Artifact locations (`research/scaffold.md`, `research/prompt-decomposition.json`, `research/loci.json`, `research/comparisons.md`, interim notes, patch / polish logs)
- The curation pass after every research session

If you need to know how hyperresearch works, read the skill file. This document does NOT duplicate step procedures — when the skill file and this file disagree, the skill file wins.

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
{hpr} note show <id1> <id2> <id3> --json   # Batch-read notes in one command
{hpr} note list --json                     # List all notes with summaries
{hpr} tags --json                          # Existing tag vocabulary
```

### Images, screenshots, and assets

```bash
{hpr} fetch "<url>" --tag <topic> --save-assets -j   # Saves screenshot + top images
{hpr} assets list --note <note-id> --json            # Assets for a specific note
{hpr} assets path <note-id> --type screenshot -j     # Get screenshot path
```

### Authenticated crawling

Login-gated content (LinkedIn, Twitter, paywalled news) needs a browser profile. Set up once via `{hpr} setup` or `crwl profiles`. Config in `.hyperresearch/config.toml` under `[web]`: `profile = "research"`, `magic = true`. LinkedIn / Twitter / Facebook / Instagram / TikTok auto-use a visible browser to avoid session kills.

If a fetch returns a login wall, tell the user to run `{hpr} setup` and create a login profile.

### Curate after every session

Every research session must end with a curation pass:

```bash
{hpr} note list --status draft -j
{hpr} note show <id> -j
{hpr} note update <id> --summary "<specific summary>" --add-tag <t> -j
{hpr} lint -j
{hpr} repair -j
{hpr} status -j
```

Lifecycle: `draft` -> `review` -> `evergreen` (or `stale` -> `deprecated` -> `archive` for outdated material).

Summaries must be specific — "Mamba achieves linear-time sequence modeling via selective state spaces" beats "Paper about Mamba". Reuse the existing tag vocabulary (`{hpr} tags -j`) rather than inventing new tags.

### Key conventions

- Notes live in `research/notes/` as markdown with YAML frontmatter
- Markdown is truth and SQLite is cache; do not make the database authoritative for note content
- Link notes with `[[note-id]]` syntax
- After editing `.md` files directly, run `{hpr} sync` to update the index
- After `research/notes/final_report_<vault_tag>.md` exists, PATCH, NEVER REGENERATE. Patcher and polish agents may revise by targeted edits only and must not overwrite or regenerate the report wholesale.
- Run `{hpr} --help` for the full command list
{end_marker}
"""
```

The `runtime_name` parameter may be unused after implementation. If it remains unused, remove it before committing so ruff stays clean.

- [ ] **Step 2: Add runtime-specific wrapper functions or constants**

Below the helper, define `HYPERRESEARCH_BLURB` and `CODEX_HYPERRESEARCH_BLURB` as format strings generated by the helper using placeholder values:

```python
HYPERRESEARCH_BLURB = _render_hyperresearch_blurb(
    marker="{marker}",
    end_marker="{end_marker}",
    hpr="{hpr}",
    runtime_name="Claude Code",
    title="Research Base (hyperresearch)",
    entrypoint="/hyperresearch <query>",
    entry_skill_path=".claude/skills/hyperresearch/SKILL.md",
    step_skill_root=".claude/skills",
    step_loading_mechanic='via `Skill(skill: "hyperresearch-N-...")` calls when each step runs',
    subagent_mechanic="Task",
    subagent_roster="fetcher, loci-analyst, depth-investigator, 4 critics, patcher, polish-auditor",
    install_steps_command="{hpr} install --steps-only . --json",
    today="{today}",
)

CODEX_HYPERRESEARCH_BLURB = _render_hyperresearch_blurb(
    marker="{marker}",
    end_marker="{end_marker}",
    hpr="{hpr}",
    runtime_name="Codex",
    title="Hyperresearch Codex Project Instructions",
    entrypoint="$hyperresearch <query>",
    entry_skill_path=".agents/skills/hyperresearch/SKILL.md",
    step_skill_root=".agents/skills",
    step_loading_mechanic="through Codex skill invocation when each step runs",
    subagent_mechanic="Codex custom-agent",
    subagent_roster="fetcher, loci-analyst, depth-investigator, source-analyst, corpus/dialectic/depth/width/instruction critics, patcher, polish-auditor, readability recommender, draft-orchestrator, synthesizer",
    install_steps_command="{hpr} install --steps-only . --codex --json",
)
```

If nested `.format(...)` placeholders become hard to read, instead create two functions `_claude_hyperresearch_blurb(...)` and `_codex_hyperresearch_blurb(...)` that call the shared renderer directly from `inject_agent_docs` and `inject_codex_agent_docs`. Preserve public constants only if tests or imports depend on them.

- [ ] **Step 3: Update injectors if needed**

If the constants remain format strings, keep the existing `inject_agent_docs` and `inject_codex_agent_docs` formatting flow. If wrapper functions are clearer, update:

```python
blurb = _claude_hyperresearch_blurb(
    marker=HYPERRESEARCH_SECTION_MARKER,
    end_marker=HYPERRESEARCH_SECTION_END,
    hpr=hpr_path,
    today=date.today().isoformat(),
)
```

and:

```python
blurb = _codex_hyperresearch_blurb(
    marker=CODEX_HYPERRESEARCH_SECTION_MARKER,
    end_marker=CODEX_HYPERRESEARCH_SECTION_END,
    hpr=hpr_path,
)
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py tests\test_core\test_codex_hooks.py tests\test_cli\test_install_codex.py tests\test_core\test_hooks.py -q
```

Expected: all focused tests pass.

- [ ] **Step 5: Run ruff**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m ruff check src tests
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit implementation**

```powershell
git add src/hyperresearch/core/agent_docs.py tests/test_core/test_codex_agent_docs.py
git commit -m "fix: render codex agents md with runtime guidance parity"
```

---

### Task 3: Verify Installed Codex AGENTS.md Output

**Files:**
- Modify: `tests/test_cli/test_install_codex.py`

- [ ] **Step 1: Add an install-level assertion**

In `test_install_codex_json_creates_vault_and_codex_assets`, after `assert (target / "AGENTS.md").exists()`, add:

```python
    agents_body = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "Run a research session with `$hyperresearch <query>`" in agents_body
    assert "Academic APIs before web search" in agents_body
    assert ".claude/skills" not in agents_body
```

- [ ] **Step 2: Run install CLI tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_cli\test_install_codex.py -q
```

Expected: all Codex install CLI tests pass.

- [ ] **Step 3: Run full focused surface tests**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests\test_core\test_codex_agent_docs.py tests\test_core\test_codex_hooks.py tests\test_cli\test_install_codex.py tests\test_core\test_hooks.py -q
```

Expected: all focused tests pass.

- [ ] **Step 4: Commit install-level test**

```powershell
git add tests/test_cli/test_install_codex.py
git commit -m "test: assert installed codex agents md guidance"
```

---

### Task 4: Final Verification

**Files:**
- No planned file changes.

- [ ] **Step 1: Run full pytest**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m pytest -q
```

Expected: full test suite passes.

- [ ] **Step 2: Run ruff**

Run:

```powershell
..\..\.venv\Scripts\python.exe -m ruff check src tests
```

Expected: `All checks passed!`

- [ ] **Step 3: Generate a sample Codex vault and inspect AGENTS.md**

Run:

```powershell
$tmp = New-Item -ItemType Directory -Force -Path "$env:TEMP\hpr-codex-agents-md-parity"
..\..\.venv\Scripts\python.exe -m hyperresearch install $tmp.FullName --codex --json
Get-Content "$($tmp.FullName)\AGENTS.md" | Select-String -Pattern "Run a research session|Academic APIs|PATCH, NEVER REGENERATE|.claude/skills"
```

Expected:

- output includes `Run a research session with `$hyperresearch <query>``
- output includes `Academic APIs before web search`
- output includes `PATCH, NEVER REGENERATE`
- output does not include `.claude/skills`

- [ ] **Step 4: Check git status**

Run:

```powershell
git status --short
```

Expected: clean working tree.
