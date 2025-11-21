"""Generate a sample dataset from a single Kiro demo episode.

This script runs the deterministic demo MAS flow and exports the result as
both JSONL and CSV for quick manual inspection.
"""
from pathlib import Path

from archelab.episodes.kiro_demo_flow import run_demo_episode
from archelab.logging_utils.dataset_writer import append_episode_jsonl, write_episodes_csv


def main() -> None:
    """Run the demo episode and export it as JSONL and CSV."""
    episode_result, trace_json = run_demo_episode()

    output_dir = Path("demo_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "episodes.jsonl"
    csv_path = output_dir / "episodes.csv"

    append_episode_jsonl(jsonl_path, episode_result, trace_json)
    write_episodes_csv(csv_path, [episode_result])

    print("Demo dataset generated:")
    print(f"  episode_id: {episode_result.episode_id}")
    print(f"  task_success: {episode_result.task_success}")
    print(f"  attack_success: {episode_result.attack_success}")
    print(f"  contains_secret_in_msg: {episode_result.contains_secret_in_msg}")
    print(f"  unauthorized_write: {episode_result.unauthorized_write}")
    print(f"  JSONL path: {jsonl_path}")
    print(f"  CSV path: {csv_path}")


if __name__ == "__main__":
    main()
