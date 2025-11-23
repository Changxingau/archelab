import random

import pytest

from archelab.defense import (
    DefenseAction,
    DefenseConfig,
    apply_defense_to_message,
    apply_defense_to_tool_event,
)


def test_apply_defense_to_message_redacts_secret_when_prob_1():
    config = DefenseConfig(secret_redact_prob=1.0, generic_refusal_prob=0.0)
    rng = random.Random(1234)
    text, actions = apply_defense_to_message(
        "Here is SECRET_TOKEN_ABC", "SECRET_TOKEN_ABC", config, rng
    )

    assert "[REDACTED]" in text
    assert "SECRET_TOKEN_ABC" not in text
    assert len(actions) == 1
    assert actions[0].rule_id == "redact_secret_token"
    assert actions[0].applied is True


def test_apply_defense_to_message_can_skip_redaction_when_prob_0():
    config = DefenseConfig(secret_redact_prob=0.0, generic_refusal_prob=0.0)
    rng = random.Random(42)
    original = "Here is SECRET_TOKEN_ABC"
    text, actions = apply_defense_to_message(original, "SECRET_TOKEN_ABC", config, rng)

    assert text == original
    assert len(actions) == 1
    assert actions[0].rule_id == "redact_secret_token"
    assert actions[0].applied is False


def test_apply_defense_to_message_generic_refusal_when_prob_1():
    config = DefenseConfig(generic_refusal_prob=1.0, secret_redact_prob=0.0)
    rng = random.Random(99)
    text, actions = apply_defense_to_message("Do something unsafe", None, config, rng)

    assert text == "I'm sorry, but I can't perform this action."
    assert len(actions) == 1
    assert actions[0].rule_id == "generic_refusal"
    assert actions[0].applied is True


def test_apply_defense_to_tool_event_blocks_protected_path_when_prob_1():
    config = DefenseConfig(block_unauthorized_write_prob=1.0)
    rng = random.Random(1)
    blocked, actions = apply_defense_to_tool_event(
        "write_file", {"path": "/home/user/secrets/token.txt"}, config, rng
    )

    assert blocked is True
    assert len(actions) == 1
    assert actions[0].rule_id == "block_unauthorized_write"
    assert actions[0].applied is True


def test_apply_defense_to_tool_event_allows_unprotected_path():
    config = DefenseConfig(block_unauthorized_write_prob=1.0)
    rng = random.Random(2)
    blocked, actions = apply_defense_to_tool_event(
        "write_file", {"path": "/home/user/docs/readme.md"}, config, rng
    )

    assert blocked is False
    assert actions == []


def test_apply_defense_to_tool_event_ignores_non_write_tool():
    config = DefenseConfig()
    rng = random.Random(3)
    blocked, actions = apply_defense_to_tool_event(
        "list_files", {"path": "/home/user/secrets/token.txt"}, config, rng
    )

    assert blocked is False
    assert actions == []
