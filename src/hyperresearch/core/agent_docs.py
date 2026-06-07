"""Agent documentation integration for Claude and Codex project docs."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Literal

HYPERRESEARCH_SECTION_MARKER = "<!-- hyperresearch:start -->"
HYPERRESEARCH_SECTION_END = "<!-- hyperresearch:end -->"
CODEX_HYPERRESEARCH_SECTION_MARKER = "<!-- hyperresearch-codex:start -->"
CODEX_HYPERRESEARCH_SECTION_END = "<!-- hyperresearch-codex:end -->"

AgentDocsRuntime = Literal["claude", "codex"]


def _read_project_doc_template() -> str:
    try:
        return (
            resources.files("hyperresearch.templates.agent_docs")
            .joinpath("hyperresearch_project.md")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError):
        return (
            Path(__file__).resolve().parent.parent
            / "templates"
            / "agent_docs"
            / "hyperresearch_project.md"
        ).read_text(encoding="utf-8")


def _runtime_context(runtime: AgentDocsRuntime, hpr_path: str, today: str) -> dict[str, str]:
    if runtime == "claude":
        return {
            "marker": HYPERRESEARCH_SECTION_MARKER,
            "end_marker": HYPERRESEARCH_SECTION_END,
            "heading": f"Research Base (hyperresearch) — Today is {today}",
            "hpr": hpr_path,
            "cli_path_note": "— use this exact path for every hyperresearch command. It may not be on your system PATH.",
            "runtime_intro": (
                f"Run `{hpr_path} install --steps-only . --json` to provision or refresh the Claude-facing skills. "
                "Claude loads the hyperresearch entry skill from `.claude/skills/hyperresearch/SKILL.md`."
            ),
            "runtime_invariants": "",
            "entry_command": "/hyperresearch <query>",
            "entry_skill_path": ".claude/skills/hyperresearch/SKILL.md",
            "step_loading_mechanism": 'the `Skill` tool when each step runs (`Skill(skill: "hyperresearch-N-...")`)',
            "spawn_contract": "every Task call passes the verbatim research_query + pipeline position + inputs",
        }

    if runtime == "codex":
        return {
            "marker": CODEX_HYPERRESEARCH_SECTION_MARKER,
            "end_marker": CODEX_HYPERRESEARCH_SECTION_END,
            "heading": "Hyperresearch Codex Project Instructions",
            "hpr": hpr_path,
            "cli_path_note": "- use this exact path for every hyperresearch command.",
            "runtime_intro": (
                "This repository is trusted for Codex project configuration under `.codex/`. Codex support is additive "
                "to Claude Code support and uses the same V8 source material.\n\n"
                f"Run `{hpr_path} install --steps-only . --codex --json` to provision Codex-facing skills, agents, and hooks/config. "
                "The entry skill lives at `.agents/skills/hyperresearch/SKILL.md`; Codex subagent definitions live under `.codex/agents/`."
            ),
            "runtime_invariants": (
                "The canonical research query is persisted at `research/query-<vault_tag>.md` and is gospel for every "
                "downstream step and subagent. Markdown is truth and SQLite is cache; do not make the database "
                "authoritative for note content.\n\n"
                "After `research/notes/final_report_<vault_tag>.md` exists, PATCH, NEVER REGENERATE. Patcher and polish "
                "agents may revise by targeted edits only and must not overwrite or regenerate the report wholesale."
            ),
            "entry_command": "$hyperresearch <query>",
            "entry_skill_path": ".agents/skills/hyperresearch/SKILL.md",
            "step_loading_mechanism": (
                "step-specific skill invocations plus the matching Codex custom-agent spawn when a role needs fresh context"
            ),
            "spawn_contract": "every Codex custom-agent spawn passes the verbatim research_query + pipeline position + inputs",
        }

    raise ValueError(f"Unknown agent docs runtime: {runtime}")


def render_agent_docs(
    runtime: AgentDocsRuntime,
    hpr_path: str = "hyperresearch",
    today: str | None = None,
) -> str:
    if today is None:
        from datetime import date

        today = date.today().isoformat()
    hpr_path = hpr_path.replace("\\", "/")
    return _read_project_doc_template().format(**_runtime_context(runtime, hpr_path, today)).strip()


def _resolve_executable() -> str:
    """Find the absolute path to the hyperresearch executable.

    Priority: venv sibling of current python > PATH > bare name.
    """
    import shutil
    import sys

    python_dir = Path(sys.executable).parent
    for name in ("hyperresearch", "hyperresearch.exe"):
        candidate = python_dir / name
        if candidate.exists():
            return str(candidate)
    for name in ("hyperresearch", "hyperresearch.exe"):
        candidate = python_dir / "Scripts" / name
        if candidate.exists():
            return str(candidate)

    which = shutil.which("hyperresearch")
    if which:
        return which

    return "hyperresearch"


def inject_agent_docs(vault_root: Path) -> list[str]:
    """Inject hyperresearch docs into CLAUDE.md at the vault root."""
    hpr_path = _resolve_executable().replace("\\", "/")
    blurb = render_agent_docs("claude", hpr_path=hpr_path)

    modified: list[str] = []
    result = _inject_into_file(vault_root / "CLAUDE.md", blurb, "CLAUDE.md")
    if result:
        modified.append(result)
    return modified


def inject_codex_agent_docs(vault_root: Path) -> list[str]:
    """Inject hyperresearch Codex docs into AGENTS.md at the vault root."""
    hpr_path = _resolve_executable().replace("\\", "/")
    blurb = render_agent_docs("codex", hpr_path=hpr_path)

    modified: list[str] = []
    result = _inject_into_file(vault_root / "AGENTS.md", blurb, "AGENTS.md")
    if result:
        modified.append(result)
    return modified


def _inject_into_file(filepath: Path, blurb: str, filename: str) -> str | None:
    """Inject the hyperresearch blurb into a single file. Returns action taken or None."""
    marker = HYPERRESEARCH_SECTION_MARKER
    end_marker = HYPERRESEARCH_SECTION_END
    if CODEX_HYPERRESEARCH_SECTION_MARKER in blurb:
        marker = CODEX_HYPERRESEARCH_SECTION_MARKER
        end_marker = CODEX_HYPERRESEARCH_SECTION_END

    if filepath.exists():
        content = filepath.read_text(encoding="utf-8-sig")

        if marker in content:
            pattern = re.compile(
                re.escape(marker) + r".*?" + re.escape(end_marker),
                re.DOTALL,
            )
            new_content = pattern.sub(lambda _: blurb.strip(), content)
            if new_content != content:
                filepath.write_text(new_content, encoding="utf-8")
                return f"{filename} (updated)"
            return None
        separator = "\n\n" if not content.endswith("\n") else "\n"
        filepath.write_text(content + separator + blurb.strip() + "\n", encoding="utf-8")
        return f"{filename} (appended)"

    filepath.parent.mkdir(parents=True, exist_ok=True)
    header = f"# {filepath.stem}\n"
    filepath.write_text(header + blurb.strip() + "\n", encoding="utf-8")
    return f"{filename} (created)"
