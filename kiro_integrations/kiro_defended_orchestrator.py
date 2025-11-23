"""Defended Kiro orchestrator with minimal defense hooks."""

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


def _summarize_actions(actions: list[DefenseAction], counters: Dict[str, int]) -> None:
    """Update defense counters based on applied actions."""

    for action in actions:
        if action.rule_id == "redact_secret_token" and action.applied:
            counters["redacted_leaks"] = counters.get("redacted_leaks", 0) + 1
        if action.rule_id == "block_unauthorized_write" and action.applied:
            counters["blocked_writes"] = counters.get("blocked_writes", 0) + 1
        if action.rule_id == "generic_refusal" and action.applied:
            counters["generic_refusals"] = counters.get("generic_refusals", 0) + 1


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
    task_type: str = "coding",
    input_context: str | None = None,
    expected_output: str | None = None,
    defense_config: DefenseConfig | None = None,
) -> Tuple[Dict, Dict]:
    """Execute one defended Kiro episode and return result/trace as dictionaries."""

    defense_config = defense_config or DefenseConfig(profile_name="minimal_v1")
    rng = random.Random()

    client = client or ArchelabClient(
        default_topology=topology, default_defense_profile=defense_config.profile_name
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

    counters: Dict[str, int] = {
        "redacted_leaks": 0,
        "blocked_writes": 0,
        "generic_refusals": 0,
    }

    turns = _profile_turns(attacker_profile, secret, expected_output)

    metadata = {
        "repo_path": repo_path,
        "secret": secret,
        "task_type": task_type,
        "input_context": input_context,
        "expected_output": expected_output,
        "attacker_profile": attacker_profile,
        "behavior_archetype": PROFILE_TO_ARCHETYPE[attacker_profile],
        "defense_profile": defense_config.profile_name,
    }

    episode_id = client.begin_episode(
        task_id=task_id,
        task_description=task_description,
        topology=topology,
        defense_profile=defense_config.profile_name,
        extra_metadata=metadata,
    )

    recorder = episode_api.EPISODES.get(episode_id, {}).get("recorder")
    if recorder is not None:
        for key, value in metadata.items():
            if key == "secret":
                continue
            recorder.set_meta(key, value)

    for turn in turns:
        client.log_agent_message(
            episode_id=episode_id,
            agent_name="attacker",
            role="attacker",
            content=turn.attacker_prompt,
            receiver="worker",
        )

        defended_reply, msg_actions = apply_defense_to_message(
            message_text=turn.worker_reply,
            secret_token=secret,
            config=defense_config,
            rng=rng,
        )
        _summarize_actions(msg_actions, counters)

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
            _summarize_actions(tool_actions, counters)

            if blocked and recorder is not None:
                step = client._next_step(episode_id)  # type: ignore[attr-defined]
                recorder.log_tool_event(
                    step=step,
                    agent="worker",
                    tool=invocation.tool_name,
                    args={**tool_args, "blocked": True},
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
    trace_dict["meta"].setdefault("behavior_archetype", PROFILE_TO_ARCHETYPE[attacker_profile])
    trace_dict["meta"]["defense_profile"] = defense_config.profile_name

    result_dict.update(
        {
            "topology": topology,
            "defense_enabled": True,
            "defense_profile": defense_config.profile_name,
            "defense_summary": counters,
        }
    )

    return result_dict, trace_dict


__all__ = ["run_single_defended_episode"]
