"""CLI tests for Claude/Codex install routing."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyperresearch.cli import app
from hyperresearch.core.hooks import _HYPERRESEARCH_STEP_SKILLS

runner = CliRunner()


class _TtyStdin:
    def __init__(self, stream):
        self._stream = stream

    def isatty(self):
        return True

    def __getattr__(self, name):
        return getattr(self._stream, name)


class _TtyCliRunner(CliRunner):
    @contextmanager
    def isolation(self, *args, **kwargs):
        with super().isolation(*args, **kwargs) as streams:
            original_stdin = sys.stdin
            sys.stdin = _TtyStdin(original_stdin)
            try:
                yield streams
            finally:
                sys.stdin = original_stdin


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
    assert data["vault_path"] == str(target.resolve())
    assert data["vault"] == "created"
    assert data["agent_docs"]
    assert data["hooks_installed"]
    assert (target / ".hyperresearch").exists()
    assert (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()
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
    assert data["steps_installed"]
    assert "Codex" in data["steps_installed"]
    assert ".agents/skills" in data["steps_installed"]
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
    assert data["runtime"] == "claude"
    assert (target / "CLAUDE.md").exists()
    assert (target / ".claude" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".codex" / "agents").exists()


def test_install_global_codex_json_uses_codex_home_locations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("hyperresearch.cli.install.Path.home", lambda: tmp_path)

    result = runner.invoke(app, ["install", "--global", "--codex", "--json"])

    data = _json_data(result)
    assert data["runtime"] == "codex"
    assert data["global"] is True
    assert data["home"] == str(tmp_path)
    assert (tmp_path / ".codex" / "AGENTS.md").exists()
    assert (tmp_path / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert (
        tmp_path / ".codex" / "agents" / "hyperresearch-patcher.toml"
    ).exists()
    assert not (tmp_path / ".claude").exists()


def test_interactive_new_vault_codex_install_stays_on_codex_path(
    tmp_path: Path,
):
    target = tmp_path / "interactive-codex-vault"
    tty_runner = _TtyCliRunner()

    result = tty_runner.invoke(
        app,
        ["install", str(target), "--codex"],
        input="\n",
    )

    assert result.exit_code == 0, result.output
    assert (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()
    assert (target / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert (
        target / ".codex" / "agents" / "hyperresearch-patcher.toml"
    ).exists()
    assert not (target / ".claude").exists()
    assert "Codex" in result.output or ".agents" in result.output or ".codex" in result.output
