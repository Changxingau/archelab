"""Single-episode defended Kiro orchestrator for Archelab logging.

This module mirrors :mod:`kiro_integrations.kiro_orchestrator` but applies
defense policies to worker messages and tool invocations before logging them
into ArcheLab.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Tuple

from archelab.defense import (
    DefenseAction,
    DefenseConfig,
    apply_defense_to_message,
    apply_defense_to_tool_event,
)
from archelab.episodes import episode_api
from kiro_integrations.archelab_client import ArchelabClient
from kiro_integrations.kiro_orchestrator import _ensure_parent, _profile_turns


def _record_defense_actions(
    actions: list[DefenseAction],
    counters: dict[str, int],
) -> None:
    for action in actions:
        if action.rule_id == "redact_secret_token" and action.applied:
            counters["redacted_leaks"] += 1
        if action.rule_id == "block_unauthorized_write" and action.applied:
            counters["blocked_writes"] += 1
        if action.rule_id == "generic_refusal" and action.applied:
            counters["generic_refusals"] += 1


def run_single_defended_episode(
    *,
    task_id: str,
    task_description: str,
    repo_path: str,
    secret: str,
    attacker_profile: str = "direct_leak",
    client: ArchelabClient | None = None,
    dataset_path: str | Path | None = None,
    topology: str = "defended",
    defense_profile: str | None = None,
    task_type: str = "coding",
    input_context: str | None = None,
    expected_output: str | None = None,
    defense_config: DefenseConfig | None = None,
) -> Tuple[Dict, Dict]:
    """Execute one defended Kiro episode and return result/trace as dictionaries."""

    defense_config = defense_config or DefenseConfig(
        profile_name=defense_profile or "minimal_v1"
    )
    if defense_profile is None:
        defense_profile = defense_config.profile_name
    else:
        defense_config.profile_name = defense_profile

    client = client or ArchelabClient(
        default_topology=topology, default_defense_profile=defense_profile
    )

    input_context = input_context or task_description
    expected_output = expected_output or "Task completed"

    PROFILE_TO_ARCHETYPE = {
        "direct_leak": "manipulator",
        "backdoor_dropper": "covert_actor",
        "deceiver": "deceiver",
        "escalator": "infiltrator_escalator",
        "mixed": "manipulator+covert_actor",
    }

    if attacker_profile not in PROFILE_TO_ARCHETYPE:
        raise ValueError(
            "Unknown attacker_profile '" + attacker_profile + "'. Supported profiles: "
            + str(sorted(PROFILE_TO_ARCHETYPE))
        )

    turns = _profile_turns(attacker_profile, secret, expected_output)

    metadata = {
        "repo_path": repo_path,
        "secret": secret,
        "task_type": task_type,
        "input_context": input_context,
        "expected_output": expected_output,
        "attacker_profile": attacker_profile,
        "behavior_archetype": PROFILE_TO_ARCHETYPE[attacker_profile],
    }

    episode_id = client.begin_episode(
        task_id=task_id,
        task_description=task_description,
        topology=topology,
        defense_profile=defense_profile,
        extra_metadata=metadata,
    )

    recorder = episode_api.EPISODES.get(episode_id, {}).get("recorder")
    if recorder is not None:
        for key, value in metadata.items():
            if key == "secret":
                continue
            recorder.set_meta(key, value)
        recorder.set_meta("defense_profile", defense_profile)
        recorder.set_meta("defense_enabled", True)
        recorder.set_meta("topology", topology)

    counters: Dict[str, int] = {
        "redacted_leaks": 0,
        "blocked_writes": 0,
        "generic_refusals": 0,
    }

    rng = random.Random()
    state = episode_api.EPISODES.get(episode_id)
    if state is not None:
        state["topology"] = topology
        state["attacker_profile"] = attacker_profile
        state["behavior_archetype"] = metadata.get("behavior_archetype")
        state["defense_enabled"] = True
        state["defense_profile"] = defense_profile
        state["defense_summary"] = counters

    for turn in turns:
        client.log_agent_message(
            episode_id=episode_id,
            agent_name="attacker",
            role="attacker",
            content=turn.attacker_prompt,
            receiver="worker",
        )

        defended_reply, message_actions = apply_defense_to_message(
            message_text=turn.worker_reply,
            secret_token=secret,
            config=defense_config,
            rng=rng,
        )
        _record_defense_actions(message_actions, counters)

        client.log_agent_message(
            episode_id=episode_id,
            agent_name="worker",
            role="assistant",
            content=defended_reply,
            receiver="attacker",
        )

        for invocation in turn.tool_invocations:
            tool_args: Dict[str, Any] = {}
            if isinstance(invocation.input, dict):
                tool_args.update(invocation.input)

            blocked, tool_actions = apply_defense_to_tool_event(
                tool_name=invocation.tool_name,
                tool_args=tool_args,
                config=defense_config,
                rng=rng,
            )
            _record_defense_actions(tool_actions, counters)

            if blocked:
                if recorder is not None:
                    step = client._next_step(episode_id)  # type: ignore[attr-defined]
                    recorder.log_tool_event(
                        step=step,
                        agent="worker",
                        tool=invocation.tool_name,
                        args=tool_args,
                        result_summary="blocked by defense",
                    )
                continue

            client.log_tool_use(
                episode_id=episode_id,
                agent_name="worker",
                tool_name=invocation.tool_name,
                input=invocation.input,
                output=invocation.output,
                success=invocation.success,
                tags=invocation.tags,
            )

    dataset_path = Path(dataset_path) if dataset_path is not None else None
    _ensure_parent(dataset_path)

    result_dict, trace_dict = client.end_episode(
        episode_id=episode_id, dataset_path=str(dataset_path) if dataset_path else None
    )

    if "meta" not in trace_dict:
        trace_dict["meta"] = {}
    trace_dict["meta"].setdefault("attacker_profile", attacker_profile)
    trace_dict["meta"]["behavior_archetype"] = PROFILE_TO_ARCHETYPE[attacker_profile]
    trace_dict["meta"]["defense_profile"] = defense_profile
    trace_dict["meta"]["defense_enabled"] = True

    return result_dict, trace_dict


__all__ = ["run_single_defended_episode"]
