"""CLI tests for Claude/Codex install routing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyperresearch.cli import app
from hyperresearch.core.hooks import _HYPERRESEARCH_STEP_SKILLS

runner = CliRunner()


@pytest.fixture(autouse=True)
def _skip_crawl4ai_setup(monkeypatch):
    monkeypatch.setattr("hyperresearch.cli.install._setup_crawl4ai", lambda vault: "not_installed")


def _json_data(result):
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    return payload["data"]


def test_install_codex_json_creates_vault_and_codex_assets(tmp_path: Path):
    target = tmp_path / "codex-vault"

    result = runner.invoke(app, ["install", str(target), "--codex", "--json"])

    data = _json_data(result)
    assert data["runtime"] == "codex"
    assert data["vault"] == "created"
    assert (target / ".hyperresearch").exists()
    assert (target / "AGENTS.md").exists()
    assert (target / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert (
        target / ".codex" / "agents" / "hyperresearch-patcher.toml"
    ).exists()
    assert not (target / ".claude").exists()


def test_install_steps_only_codex_json_writes_all_step_skills(tmp_path: Path):
    target = tmp_path / "codex-steps"

    result = runner.invoke(
        app,
        ["install", str(target), "--steps-only", "--codex", "--json"],
    )

    data = _json_data(result)
    assert data["runtime"] == "codex"
    assert data["target"] == str(target.resolve())
    for skill_name in _HYPERRESEARCH_STEP_SKILLS:
        assert (
            target / ".agents" / "skills" / skill_name / "SKILL.md"
        ).exists(), f"missing Codex step skill: {skill_name}"
    assert not (target / ".codex" / "agents").exists()
    assert not (target / ".claude").exists()


def test_install_json_defaults_to_claude_behavior(tmp_path: Path):
    target = tmp_path / "claude-vault"

    result = runner.invoke(app, ["install", str(target), "--json"])

    data = _json_data(result)
    assert data.get("runtime", "claude") == "claude"
    assert (target / "CLAUDE.md").exists()
    assert (target / ".claude" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".codex" / "agents").exists()


def test_generated_codex_steps_only_command_is_accepted(tmp_path: Path):
    target = tmp_path / "codex-doc-command"

    result = runner.invoke(
        app,
        ["install", str(target), "--steps-only", "--codex", "--json"],
    )

    assert result.exit_code == 0, result.output
