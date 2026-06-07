from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyperresearch.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _skip_crawl4ai_setup(monkeypatch):
    monkeypatch.setattr("hyperresearch.cli.install._setup_crawl4ai", lambda vault: "not_installed")


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

    result = runner.invoke(app, ["config", "agent-docs", "--codex", "--json"])

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

    result = runner.invoke(app, ["config", "agent-docs", "--claude", "--codex", "--json"])

    assert result.exit_code != 0
    assert "Choose only one runtime" in result.output


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


def test_repair_no_docs_ignores_runtime_flags_and_omits_runtime_json(tmp_path: Path, monkeypatch):
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
            "--no-docs",
            "--claude",
            "--codex",
            "--json",
        ],
    )

    data = _json_data(result)
    assert "agent_docs_runtime" not in data
