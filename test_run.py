from pathlib import Path
from tempfile import TemporaryDirectory

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

# Basic smoke test for dataset_writer.append_episode_jsonl
with TemporaryDirectory() as tmpdir:
    jsonl_path = Path(tmpdir) / "episodes.jsonl"
    append_episode_jsonl(jsonl_path, result, trace)
    with jsonl_path.open("r", encoding="utf-8") as fp:
        lines = fp.readlines()
    assert len(lines) >= 1
