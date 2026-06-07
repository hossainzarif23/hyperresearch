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

STALE_CLAUDE_MECHANICS = (
    "Task call",
    "Task calls",
    "Task prompt",
    "Task result",
)


def test_adapt_codex_skill_content_rewrites_claude_mechanics():
    source = (
        "If `.claude/skills/hyperresearch-1-decompose/SKILL.md` is missing, "
        "run `hyperresearch install --steps-only . --json`. "
        'Then call `Skill(skill: "hyperresearch-1-decompose")`. '
        "Spawn via the Task tool with `subagent_type: hyperresearch-patcher`. "
        "Use subagent_type: hyperresearch-<critic-name>-critic for each critic. "
        "Every Task call passes the query. Batch Task calls carefully."
    )

    adapted = _adapt_codex_skill_content(source)

    assert "Use subagent_type: hyperresearch-<critic-name>-critic for each critic." in source
    assert "Every Task call passes the query. Batch Task calls carefully." in source
    assert ".agents/skills/hyperresearch-1-decompose/SKILL.md" in adapted
    assert "hyperresearch install --steps-only . --codex --json" in adapted
    assert "$hyperresearch-1-decompose" in adapted
    assert "spawn the Codex custom agent `hyperresearch-patcher`" in adapted
    assert "spawn the Codex custom agent `hyperresearch-<critic-name>-critic`" in adapted
    assert ".claude/skills" not in adapted
    assert "Skill(skill:" not in adapted
    assert "Task tool" not in adapted
    for stale_term in STALE_CLAUDE_MECHANICS:
        assert stale_term not in adapted


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
    hpr_path = "C:/Tools/hpr.exe"
    result = _install_codex_hyperresearch_step_skills(tmp_vault.root, hpr_path=hpr_path)

    assert result is not None
    skills_root = tmp_vault.root / ".agents" / "skills"
    for skill_name in _HYPERRESEARCH_STEP_SKILLS:
        skill_path = skills_root / skill_name / "SKILL.md"
        assert skill_path.exists(), f"missing Codex step skill: {skill_name}"
        body = skill_path.read_text(encoding="utf-8")
        assert f"name: {skill_name}" in body
        assert ".claude/skills" not in body
        assert "{hpr_path}" not in body
        for stale_term in STALE_CLAUDE_MECHANICS:
            assert stale_term not in body
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
    assert data["model_reasoning_effort"] == "medium"
    instructions = data["developer_instructions"]
    assert "tools: Read, Edit" not in instructions
    assert "Codex custom-agent note" in instructions
    assert "PATCH" in instructions
    assert "regenerat" in instructions.lower()
    assert "research/patch-log.json" in instructions


def test_install_codex_hooks_registers_project_roster(tmp_path):
    actions = install_codex_hooks(tmp_path, "hyperresearch")

    assert actions
    assert (tmp_path / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert not (tmp_path / ".claude" / "settings.json").exists()
    assert not (tmp_path / "CLAUDE.md").exists()
    for filename in CODEX_AGENT_FILENAMES:
        assert (tmp_path / ".codex" / "agents" / filename).exists()


def test_install_codex_hooks_writes_valid_custom_agent_toml(tmp_path):
    result = install_codex_hooks(tmp_path, "C:/Tools/hpr.exe")

    assert result
    agents_root = tmp_path / ".codex" / "agents"
    required_fields = {
        "name",
        "description",
        "developer_instructions",
        "model",
        "model_reasoning_effort",
    }
    forbidden_terms = (*STALE_CLAUDE_MECHANICS, "{hpr_path}", "subagent_type:")
    for filename in CODEX_AGENT_FILENAMES:
        agent_path = agents_root / filename
        assert agent_path.exists(), f"missing Codex custom agent: {filename}"
        data = tomllib.loads(agent_path.read_text(encoding="utf-8"))
        assert required_fields <= data.keys()
        instructions = data["developer_instructions"]
        for forbidden_term in forbidden_terms:
            assert forbidden_term not in instructions


def test_install_codex_hooks_applies_custom_agent_model_policy(tmp_path):
    install_codex_hooks(tmp_path, "hyperresearch")

    agents_root = tmp_path / ".codex" / "agents"
    patcher = tomllib.loads((agents_root / "hyperresearch-patcher.toml").read_text(encoding="utf-8"))
    polish = tomllib.loads((agents_root / "hyperresearch-polish-auditor.toml").read_text(encoding="utf-8"))
    fetcher = tomllib.loads((agents_root / "hyperresearch-fetcher.toml").read_text(encoding="utf-8"))
    draft = tomllib.loads((agents_root / "hyperresearch-draft-orchestrator.toml").read_text(encoding="utf-8"))
    synthesizer = tomllib.loads((agents_root / "hyperresearch-synthesizer.toml").read_text(encoding="utf-8"))

    assert patcher["model"] == "gpt-5.5"
    assert patcher["model_reasoning_effort"] == "medium"
    assert polish["model"] == "gpt-5.5"
    assert polish["model_reasoning_effort"] == "medium"

    assert fetcher["model"] == "gpt-5.4-mini"
    assert fetcher["model_reasoning_effort"] == "medium"
    assert draft["model"] == "gpt-5.4-mini"
    assert draft["model_reasoning_effort"] == "medium"
    assert synthesizer["model"] == "gpt-5.4-mini"
    assert synthesizer["model_reasoning_effort"] == "medium"


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
