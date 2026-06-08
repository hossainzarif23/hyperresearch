from __future__ import annotations

from typing import Any, cast

import pytest

from hyperresearch.core.agent_docs import (
    CODEX_HYPERRESEARCH_SECTION_END,
    CODEX_HYPERRESEARCH_SECTION_MARKER,
    HYPERRESEARCH_SECTION_END,
    HYPERRESEARCH_SECTION_MARKER,
    inject_codex_agent_docs,
    render_agent_docs,
)


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


def test_render_agent_docs_preserves_load_bearing_guidance_for_both_runtimes():
    required = (
        "Paths in this document are relative to your current working directory",
        "Do NOT use WebFetch for source pages",
        "The skill files own everything about how to research",
        "research/query-<vault_tag>.md",
        "Markdown is truth and SQLite is cache",
        "PATCH, NEVER REGENERATE",
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
        for item in required:
            assert item in body


def test_render_agent_docs_uses_runtime_specific_mechanics():
    claude = render_agent_docs("claude", hpr_path="C:/Tools/hyperresearch.exe", today="2026-06-07")
    codex = render_agent_docs("codex", hpr_path="C:/Tools/hyperresearch.exe", today="2026-06-07")

    assert HYPERRESEARCH_SECTION_MARKER in claude
    assert HYPERRESEARCH_SECTION_END in claude
    assert "/hyperresearch <query>" in claude
    assert ".claude/skills/hyperresearch/SKILL.md" in claude
    assert 'Skill(skill: "hyperresearch-N-' in claude
    assert "Task call" in claude

    assert CODEX_HYPERRESEARCH_SECTION_MARKER in codex
    assert CODEX_HYPERRESEARCH_SECTION_END in codex
    assert "$hyperresearch <query>" in codex
    assert ".agents/skills/hyperresearch/SKILL.md" in codex
    assert ".codex/agents/" in codex
    assert "Codex custom-agent spawn" in codex
    assert "when a role needs fresh context" not in codex

    assert ".claude/skills" not in codex
    assert "/hyperresearch <query>" not in codex
    assert "Task call" not in codex
    assert "Task calls" not in codex
    assert "Task tool" not in codex


def test_render_agent_docs_shares_invariants_across_runtimes():
    claude = render_agent_docs("claude", hpr_path="C:/Tools/hyperresearch.exe", today="2026-06-07")
    codex = render_agent_docs("codex", hpr_path="C:/Tools/hyperresearch.exe", today="2026-06-07")

    for body in (claude, codex):
        assert "Markdown is truth and SQLite is cache" in body
        assert "PATCH, NEVER REGENERATE" in body


def test_render_agent_docs_normalizes_windows_hpr_path_for_direct_calls():
    body = render_agent_docs("codex", hpr_path=r"C:\Tools\hyperresearch.exe", today="2026-06-07")

    assert "C:/Tools/hyperresearch.exe" in body
    assert r"C:\Tools" not in body


def test_render_agent_docs_returns_stripped_output_for_direct_calls():
    body = render_agent_docs("codex", hpr_path="hyperresearch", today="2026-06-07")

    assert body == body.strip()


def test_render_agent_docs_rejects_unknown_runtime():
    with pytest.raises(ValueError, match="Unknown agent docs runtime"):
        render_agent_docs(cast(Any, "gemini"))


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
    assert "Do NOT use WebFetch for source pages" in body
    assert "Academic APIs before web search" in body
    assert "Curate after every session" in body
    assert ".claude/skills" not in body
    assert "/hyperresearch <query>" not in body
    assert "Task call" not in body
    assert (
        "C:/venv/Scripts/hyperresearch.exe install --steps-only . --codex --json"
        in body
    )
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
