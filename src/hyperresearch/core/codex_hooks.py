"""Codex installer for Hyperresearch skills and custom agents."""

from __future__ import annotations

import json
import re
from pathlib import Path

from hyperresearch.core.agent_docs import inject_codex_agent_docs
from hyperresearch.core.hooks import (
    _HYPERRESEARCH_STEP_SKILLS,
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


def _adapt_codex_skill_content(content: str, hpr_path: str = "hyperresearch") -> str:
    """Adapt canonical Claude skill text for Codex project skill installation."""
    adapted = content.replace("{hpr_path}", hpr_path)
    adapted = adapted.replace(".claude/skills/", ".agents/skills/")
    adapted = adapted.replace(
        "hyperresearch install --steps-only . --json",
        "hyperresearch install --steps-only . --codex --json",
    )
    adapted = re.sub(
        r'Skill\(skill: "([^"]+)"\)',
        lambda match: f"${match.group(1)}",
        adapted,
    )
    adapted = adapted.replace("Task calls", "Codex custom-agent spawns")
    adapted = adapted.replace("Task call", "Codex custom-agent spawn")
    adapted = adapted.replace("Task prompt", "custom-agent prompt")
    adapted = adapted.replace("Task result", "custom-agent result")
    adapted = adapted.replace("Task tool", "Codex subagent workflow")
    adapted = re.sub(
        r"subagent_type: ([A-Za-z0-9_<>\-]+)",
        lambda match: f"spawn the Codex custom agent `{match.group(1)}`",
        adapted,
    )
    return adapted.replace("via the Task", "by spawning the matching Codex custom agent")


def _write_skill_file(root: Path, skill_name: str, content: str, label: str) -> str | None:
    skill_dir = root / ".agents" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    dest_path = skill_dir / "SKILL.md"
    if dest_path.exists() and dest_path.read_text(encoding="utf-8") == content:
        return None
    dest_path.write_text(content, encoding="utf-8")
    return f"Codex: .agents/skills/{skill_name}/SKILL.md ({label})"


def _install_codex_hyperresearch_skill(root: Path, hpr_path: str = "hyperresearch") -> str | None:
    content = _read_skill_source("hyperresearch.md")
    if content is None:
        return None
    return _write_skill_file(
        root,
        "hyperresearch",
        _adapt_codex_skill_content(content, hpr_path),
        "$hyperresearch entry skill",
    )


def _install_codex_hyperresearch_step_skills(root: Path, hpr_path: str = "hyperresearch") -> str | None:
    installed: list[str] = []
    for skill_name in _HYPERRESEARCH_STEP_SKILLS:
        content = _read_skill_source(f"{skill_name}.md")
        if content is None:
            continue
        result = _write_skill_file(
            root,
            skill_name,
            _adapt_codex_skill_content(content, hpr_path),
            "V8 step skill",
        )
        if result:
            installed.append(skill_name)
    if not installed:
        return None
    return f"Codex: .agents/skills/hyperresearch-N-*/SKILL.md ({len(installed)} step skills)"


def _extract_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content

    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content

    data: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in content[4:end].splitlines():
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

    return data, content[end + 5 :]


def _codex_model_for(agent_name: str, claude_model: str) -> tuple[str, str]:
    high_reasoning_roles = (
        "patcher",
        "polish",
        "critic",
        "synthesizer",
        "draft-orchestrator",
    )
    if claude_model == "opus" or any(role in agent_name for role in high_reasoning_roles):
        return "gpt-5.5", "high"
    return "gpt-5.5", "medium"


def _adapt_agent_body_for_codex(body: str, tools: str) -> str:
    note = (
        "Codex custom-agent note: this TOML file preserves the Claude role and "
        f"tool restriction intent (Claude allowed tool list [{tools}]), but Codex "
        "custom agents do not document an exact Claude frontmatter tool-lock "
        "equivalent. Follow the allowed and forbidden behaviors below exactly. "
        "Do not claim exact mechanical tool-lock parity unless project Codex "
        "hooks/config enforce it. PATCH, NEVER REGENERATE: after the final "
        "report exists, make surgical edits only and never overwrite or "
        "regenerate the report wholesale.\n\n"
    )
    adapted = body.replace("Task calls", "Codex custom-agent spawns")
    adapted = adapted.replace("Task call", "Codex custom-agent spawn")
    adapted = adapted.replace("Task prompt", "custom-agent prompt")
    adapted = adapted.replace("Task result", "custom-agent result")
    adapted = adapted.replace("Task tool", "Codex subagent workflow")
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
    tools = frontmatter.get("tools", "unspecified")
    model, reasoning = _codex_model_for(name, frontmatter.get("model", "sonnet"))
    instructions = _adapt_agent_body_for_codex(body, tools).replace("{hpr_path}", hpr_path)
    return "\n".join(
        (
            f"name = {json.dumps(name)}",
            f"description = {json.dumps(description)}",
            f"model = {json.dumps(model)}",
            f"model_reasoning_effort = {json.dumps(reasoning)}",
            f"developer_instructions = {json.dumps(instructions)}",
            "",
        )
    )


def _write_codex_agent_file(root: Path, filename: str, content: str, label: str) -> str | None:
    agents_dir = root / ".codex" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    agent_path = agents_dir / filename
    if agent_path.exists() and agent_path.read_text(encoding="utf-8") == content:
        return None
    agent_path.write_text(content, encoding="utf-8")
    return f"Codex: .codex/agents/{filename} ({label})"


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
    hpr_posix = hpr_path.replace("\\", "/")
    agent_specs = (
        ("hyperresearch-fetcher.toml", RESEARCHER_AGENT.format(hpr_path=hpr_posix), "fetcher custom agent"),
        ("hyperresearch-loci-analyst.toml", LOCI_ANALYST_AGENT.format(hpr_path=hpr_posix), "loci analyst custom agent"),
        (
            "hyperresearch-depth-investigator.toml",
            DEPTH_INVESTIGATOR_AGENT.format(hpr_path=hpr_posix),
            "depth investigator custom agent",
        ),
        (
            "hyperresearch-source-analyst.toml",
            SOURCE_ANALYST_AGENT.format(hpr_path=hpr_posix),
            "source analyst custom agent",
        ),
        (
            "hyperresearch-corpus-critic.toml",
            CORPUS_CRITIC_AGENT.replace("{hpr_path}", hpr_posix),
            "corpus critic custom agent",
        ),
        (
            "hyperresearch-dialectic-critic.toml",
            DIALECTIC_CRITIC_AGENT.format(hpr_path=hpr_posix),
            "dialectic critic custom agent",
        ),
        (
            "hyperresearch-depth-critic.toml",
            DEPTH_CRITIC_AGENT.format(hpr_path=hpr_posix),
            "depth critic custom agent",
        ),
        (
            "hyperresearch-width-critic.toml",
            WIDTH_CRITIC_AGENT.format(hpr_path=hpr_posix),
            "width critic custom agent",
        ),
        (
            "hyperresearch-instruction-critic.toml",
            INSTRUCTION_CRITIC_AGENT,
            "instruction critic custom agent",
        ),
        ("hyperresearch-patcher.toml", PATCHER_AGENT, "patcher custom agent"),
        (
            "hyperresearch-polish-auditor.toml",
            POLISH_AUDITOR_AGENT.format(
                scaffold_only_sections=_render_scaffold_only_bullets(indent="- "),
            ),
            "polish auditor custom agent",
        ),
        (
            "hyperresearch-readability-recommender.toml",
            READABILITY_REFORMATTER_AGENT,
            "readability recommender custom agent",
        ),
        (
            "hyperresearch-draft-orchestrator.toml",
            DRAFT_ORCHESTRATOR_AGENT.replace("{hpr_path}", hpr_posix),
            "draft orchestrator custom agent",
        ),
        ("hyperresearch-synthesizer.toml", SYNTHESIZER_AGENT, "synthesizer custom agent"),
    )

    result = _install_codex_hyperresearch_skill(root, hpr_posix)
    if result:
        actions.append(result)

    result = _install_codex_hyperresearch_step_skills(root, hpr_posix)
    if result:
        actions.append(result)

    for filename, content, label in agent_specs:
        result = _install_agent(root, filename, content, label, hpr_posix)
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
