import csv
import json

from archelab.logging_utils.dataset_writer import append_episode_jsonl, write_episodes_csv
from archelab.models.episode_result import EpisodeResult


def make_episode(episode_id: str) -> EpisodeResult:
    return EpisodeResult(
        episode_id=episode_id,
        framework="kiro",
        topology="chain",
        task_id="task-123",
        task_type="coding",
        input_context="input",
        expected_output="output",
        worker_output="worker result",
        task_success=True,
        attack_success=False,
        attack_type=None,
        contains_secret_in_msg=False,
        unauthorized_write=None,
        steps=2,
        defense_enabled=None,
        episode_notes=None,
    )


def test_append_episode_jsonl(tmp_path):
    path = tmp_path / "episodes.jsonl"
    trace = {"messages": [{"step": 0, "role": "worker", "content": "hi"}]}

    append_episode_jsonl(path, make_episode("ep-1"), trace)
    append_episode_jsonl(path, make_episode("ep-2"), trace)

    lines = path.read_text().splitlines()
    assert len(lines) == 2

    first_entry = json.loads(lines[0])
    assert first_entry["episode_id"] == "ep-1"
    assert "trace" in first_entry
    assert first_entry["trace"]["messages"][0]["content"] == "hi"


def test_write_episodes_csv(tmp_path):
    path = tmp_path / "episodes.csv"
    episodes = [make_episode("ep-1"), make_episode("ep-2")]

    write_episodes_csv(path, episodes)

    with path.open() as csvfile:
        rows = list(csv.reader(csvfile))

    assert len(rows) >= 3  # header + two data rows
    header = rows[0]
    assert "episode_id" in header
