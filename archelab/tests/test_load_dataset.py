import json

import pytest

pd = pytest.importorskip("pandas")

from analysis.load_dataset import REQUIRED_COLUMNS, load_episodes


def test_load_episodes_basic_steps(tmp_path):
    jsonl_path = tmp_path / "episodes.jsonl"
    entry = {
        "episode_id": 1,
        "attacker_profile": "direct_leak",
        "behavior_archetype": "manipulator",
        "topology": "insecure",
        "task_success": 1,
        "attack_success": 0,
        "unauthorized_write": 0,
        "contains_secret_in_msg": 0,
        "steps": 5,
    }
    jsonl_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    assert len(df) == 1
    assert all(col in df.columns for col in REQUIRED_COLUMNS)
    assert df.loc[0, "steps"] == 5


def test_load_episodes_derives_steps_from_trace(tmp_path):
    jsonl_path = tmp_path / "episodes.jsonl"
    entry = {
        "episode_id": 2,
        "attacker_profile": "backdoor_dropper",
        "behavior_archetype": "covert_actor",
        "topology": "insecure",
        "task_success": 0,
        "attack_success": 1,
        "unauthorized_write": 1,
        "contains_secret_in_msg": 1,
        "trace": {"messages": [{"role": "user"}, {"role": "assistant"}, {"role": "attacker"}]},
    }
    jsonl_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    episode_row = df.loc[df["episode_id"] == 2].iloc[0]
    assert episode_row["steps"] == 3


def test_load_episodes_meta_fallback(tmp_path):
    jsonl_path = tmp_path / "episodes.jsonl"
    entry = {"episode_id": 3, "meta": {"foo": "bar"}}
    jsonl_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    episode_row = df.loc[df["episode_id"] == 3].iloc[0]
    assert episode_row["extra_metadata"] == {"foo": "bar"}


def test_load_episodes_skips_invalid_lines(tmp_path):
    jsonl_path = tmp_path / "episodes.jsonl"
    valid_entry = {"episode_id": 4, "steps": 2}
    content = json.dumps(valid_entry) + "\n" + "{not valid json}\n"
    jsonl_path.write_text(content, encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    assert len(df) == 1
    assert df.loc[0, "episode_id"] == 4
