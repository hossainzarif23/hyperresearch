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
