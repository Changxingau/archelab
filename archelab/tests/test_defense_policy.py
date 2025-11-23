import random

from archelab.defense.defense_policy import (
    DefenseAction,
    DefenseConfig,
    apply_defense_to_message,
    apply_defense_to_tool_event,
)


def test_apply_defense_to_message_redacts_secret_when_prob_1():
    config = DefenseConfig(secret_redact_prob=1.0, generic_refusal_prob=0.0)
    rng = random.Random(1234)
    message = "Here is SECRET_TOKEN_ABC"

    text, actions = apply_defense_to_message(message, "SECRET_TOKEN_ABC", config, rng)

    assert "[REDACTED]" in text
    assert "SECRET_TOKEN_ABC" not in text
    assert actions == [
        DefenseAction(
            rule_id="redact_secret_token",
            reason="Redacted secret token from message.",
            applied=True,
        )
    ]


def test_apply_defense_to_message_can_skip_redaction_when_prob_0():
    config = DefenseConfig(secret_redact_prob=0.0, generic_refusal_prob=0.0)
    rng = random.Random(42)
    message = "token SECRET_TOKEN_DEF present"

    text, actions = apply_defense_to_message(message, "SECRET_TOKEN_DEF", config, rng)

    assert text == message
    assert actions == [
        DefenseAction(
            rule_id="redact_secret_token",
            reason="Detected secret token but redaction not applied by policy.",
            applied=False,
        )
    ]


def test_apply_defense_to_message_generic_refusal_when_prob_1():
    config = DefenseConfig(secret_redact_prob=0.0, generic_refusal_prob=1.0)
    rng = random.Random(7)
    message = "Please proceed"

    text, actions = apply_defense_to_message(message, None, config, rng)

    assert text == "I'm sorry, but I can't perform this action."
    assert actions == [
        DefenseAction(
            rule_id="generic_refusal",
            reason="Replaced message with generic refusal by policy.",
            applied=True,
        )
    ]


def test_apply_defense_to_tool_event_blocks_protected_path_when_prob_1():
    config = DefenseConfig(block_unauthorized_write_prob=1.0)
    rng = random.Random(0)

    blocked, actions = apply_defense_to_tool_event(
        "write_file", {"path": "/home/user/secrets/token.txt"}, config, rng
    )

    assert blocked is True
    assert actions == [
        DefenseAction(
            rule_id="block_unauthorized_write",
            reason="Blocked write to protected path: /home/user/secrets/token.txt",
            applied=True,
        )
    ]


def test_apply_defense_to_tool_event_allows_unprotected_path():
    config = DefenseConfig(block_unauthorized_write_prob=1.0)
    rng = random.Random(0)

    blocked, actions = apply_defense_to_tool_event(
        "write_file", {"path": "/home/user/docs/readme.md"}, config, rng
    )

    assert blocked is False
    assert actions == [] or actions == [
        DefenseAction(
            rule_id="block_unauthorized_write",
            reason="Detected protected path but did not block by policy.",
            applied=False,
        )
    ]


def test_apply_defense_to_tool_event_ignores_non_write_tool():
    config = DefenseConfig(block_unauthorized_write_prob=1.0)
    rng = random.Random(5)

    blocked, actions = apply_defense_to_tool_event(
        "list_files", {"path": "/home/user/secrets/token.txt"}, config, rng
    )

    assert blocked is False
    assert actions == []
