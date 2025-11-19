from archelab.episodes.runner_minimal import run_episode

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
