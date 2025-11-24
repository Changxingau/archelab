import json
import csv

from archelab.logging_utils.dataset_writer import append_episode_jsonl, write_episodes_csv
from archelab.models.episode_result import EpisodeResult


def make_episode(episode_id: str) -> EpisodeResult:
    return EpisodeResult(
        episode_id=episode_id,
        framework="kiro",
        topology="chain",
        task_id="task",
        task_type="coding",
        input_context="context",
        expected_output="expected",
        worker_output="worker",
        task_success=True,
        attack_success=False,
        attack_type=None,
        contains_secret_in_msg=False,
        leakage=False,
        unauthorized_write=None,
        steps=2,
        defense_enabled=False,
        defense_profile=None,
        defense_summary={},
        episode_notes=None,
    )


def test_append_episode_jsonl(tmp_path):
    output_path = tmp_path / "episodes.jsonl"
    trace = {"messages": [{"step": 0, "content": "hello"}]}

    append_episode_jsonl(output_path, make_episode("ep1"), trace)
    append_episode_jsonl(output_path, make_episode("ep2"), trace)

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first_record = json.loads(lines[0])
    assert first_record["episode_id"] == "ep1"
    assert "trace" in first_record
    assert first_record["trace"].get("messages")


def test_write_episodes_csv(tmp_path):
    output_path = tmp_path / "episodes.csv"
    results = [make_episode("ep1"), make_episode("ep2")]

    write_episodes_csv(output_path, results)

    assert output_path.exists()

    with output_path.open("r", encoding="utf-8", newline="") as f:
        reader = list(csv.reader(f))

    assert len(reader) >= 3  # header + two rows
    header = reader[0]
    assert "episode_id" in header


def test_episode_result_to_row_includes_defense_fields():
    result = EpisodeResult(
        episode_id="ep_defended",
        framework="kiro",
        topology="defended",
        task_id="task",
        task_type="coding",
        input_context="context",
        expected_output="expected",
        worker_output="worker",
        task_success=True,
        attack_success=False,
        attack_type=None,
        contains_secret_in_msg=False,
        leakage=False,
        unauthorized_write=None,
        steps=3,
        defense_enabled=True,
        defense_profile="minimal_v1",
        defense_summary={
            "redacted_leaks": 2,
            "blocked_writes": 1,
            "generic_refusals": 0,
        },
        episode_notes=None,
    )

    rows = list(write_rows([result]))
    assert rows[0]["defense_enabled"] is True
    assert rows[0]["defense_profile"] == "minimal_v1"
    assert rows[0]["defense_redacted_leaks"] == 2
    assert rows[0]["defense_blocked_writes"] == 1
    assert rows[0]["defense_generic_refusals"] == 0


def test_episode_result_to_row_defaults_for_insecure():
    result = EpisodeResult(
        episode_id="ep_insecure",
        framework="kiro",
        topology="insecure",
        task_id="task",
        task_type="coding",
        input_context="context",
        expected_output="expected",
        worker_output="worker",
        task_success=True,
        attack_success=False,
        attack_type=None,
        contains_secret_in_msg=False,
        leakage=False,
        unauthorized_write=None,
        steps=1,
        defense_enabled=False,
        defense_profile=None,
        defense_summary={},
        episode_notes=None,
    )

    rows = list(write_rows([result]))
    assert rows[0]["defense_enabled"] is False
    assert rows[0]["defense_profile"] == "none"
    assert rows[0]["defense_redacted_leaks"] == 0
    assert rows[0]["defense_blocked_writes"] == 0
    assert rows[0]["defense_generic_refusals"] == 0


def write_rows(results):
    from archelab.logging_utils.dataset_writer import episode_result_to_row

    for res in results:
        yield episode_result_to_row(res)
