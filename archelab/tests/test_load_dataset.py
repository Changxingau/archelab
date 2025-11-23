import json

from analysis.load_dataset import REQUIRED_COLUMNS, load_episodes


def test_load_episodes_with_explicit_steps(tmp_path):
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

    jsonl_path = tmp_path / "episodes.jsonl"
    jsonl_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    assert len(df) == 1
    assert set(REQUIRED_COLUMNS).issubset(df.columns)
    assert df.loc[0, "steps"] == 5


def test_load_episodes_derives_steps_from_trace(tmp_path):
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

    jsonl_path = tmp_path / "episodes.jsonl"
    jsonl_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    assert df.loc[df["episode_id"] == 2, "steps"].iloc[0] == 3


def test_extra_metadata_falls_back_to_meta(tmp_path):
    entry = {"episode_id": 3, "meta": {"foo": "bar"}}

    jsonl_path = tmp_path / "episodes.jsonl"
    jsonl_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    assert df.loc[df["episode_id"] == 3, "extra_metadata"].iloc[0] == {"foo": "bar"}


def test_invalid_json_lines_are_skipped(tmp_path):
    valid_entry = {"episode_id": 4, "steps": 1}
    invalid_line = "{not valid json}"

    jsonl_path = tmp_path / "episodes.jsonl"
    jsonl_path.write_text(json.dumps(valid_entry) + "\n" + invalid_line + "\n", encoding="utf-8")

    df = load_episodes(str(jsonl_path))

    assert len(df) == 1
    assert df.loc[0, "episode_id"] == 4
