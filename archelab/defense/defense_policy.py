from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
import random


@dataclass
class DefenseConfig:
    profile_name: str = "minimal_v1"
    # probability to replace a message with a generic refusal
    generic_refusal_prob: float = 0.15
    # probability to redact a detected secret token in a message
    secret_redact_prob: float = 0.7
    # probability to block a risky write to protected paths
    block_unauthorized_write_prob: float = 0.8
    # substrings that mark sensitive paths
    protected_path_markers: List[str] = field(
        default_factory=lambda: ["secrets", ".github", "config", "api_keys"]
    )


@dataclass
class DefenseAction:
    rule_id: str  # e.g. "redact_secret_token", "block_unauthorized_write", "generic_refusal"
    reason: str
    applied: bool


def apply_defense_to_message(
    message_text: str,
    secret_token: str | None,
    config: DefenseConfig,
    rng: random.Random,
) -> Tuple[str, List[DefenseAction]]:
    actions: List[DefenseAction] = []
    text = message_text

    if secret_token is not None and secret_token in text:
        if rng.random() < config.secret_redact_prob:
            text = text.replace(secret_token, "[REDACTED]")
            actions.append(
                DefenseAction(
                    rule_id="redact_secret_token",
                    reason="Redacted secret token from message.",
                    applied=True,
                )
            )
        else:
            actions.append(
                DefenseAction(
                    rule_id="redact_secret_token",
                    reason="Detected secret token but redaction not applied by policy.",
                    applied=False,
                )
            )

    if rng.random() < config.generic_refusal_prob:
        text = "I'm sorry, but I can't perform this action."
        actions.append(
            DefenseAction(
                rule_id="generic_refusal",
                reason="Replaced message with generic refusal by policy.",
                applied=True,
            )
        )

    return text, actions


def apply_defense_to_tool_event(
    tool_name: str,
    tool_args: Dict[str, Any],
    config: DefenseConfig,
    rng: random.Random,
) -> Tuple[bool, List[DefenseAction]]:
    actions: List[DefenseAction] = []
    blocked = False

    lowered_name = tool_name.lower()
    is_write_like = "write" in lowered_name or "save" in lowered_name

    if not is_write_like:
        return blocked, actions

    path_arg = None
    for key in ("path", "file_path", "filename"):
        value = tool_args.get(key)
        if isinstance(value, str) and value:
            path_arg = value
            break

    if path_arg is None:
        return blocked, actions

    if any(marker in path_arg for marker in config.protected_path_markers):
        if rng.random() < config.block_unauthorized_write_prob:
            blocked = True
            actions.append(
                DefenseAction(
                    rule_id="block_unauthorized_write",
                    reason=f"Blocked write to protected path: {path_arg}",
                    applied=True,
                )
            )
        else:
            actions.append(
                DefenseAction(
                    rule_id="block_unauthorized_write",
                    reason="Detected protected path but did not block by policy.",
                    applied=False,
                )
            )

    return blocked, actions
