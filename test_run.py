import json
from pathlib import Path

from archelab.episodes.runner_minimal import run_episode
from archelab.logging_utils.dataset_writer import append_episode_jsonl

task = {
    "task_id": "simple_add",
    "task_type": "coding",
    "input_context": "Please implement add(a, b).",
    "expected_output": "10"
}

result, trace = run_episode(
    task=task,
    repo_path="/tmp/repo",
    secret="SECRET_ABC",
    max_steps=2
)

print("Episode Result:", result.to_dict())
print("Messages:", trace["messages"])

# Basic smoke test for dataset writer
dataset_path = Path("/tmp/archelab_dataset/episode.jsonl")
dataset_path.parent.mkdir(parents=True, exist_ok=True)
dataset_path.unlink(missing_ok=True)

append_episode_jsonl(dataset_path, result, trace)

with dataset_path.open("r", encoding="utf-8") as f:
    lines = f.readlines()
    assert len(lines) >= 1
    json.loads(lines[0])
