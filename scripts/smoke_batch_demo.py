"""Minimal smoke-test batch runner for deterministic demo episodes."""

from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Iterable
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from archelab.models.episode_result import EpisodeResult
from scripts.run_batch_demo import _run_single_demo_episode

NUM_EPISODES = 10
OUTPUT_JSONL = Path("demo_data/smoke_episodes.jsonl")
TOPOLOGY = "insecure"


def _aggregate_counts(results: Iterable[EpisodeResult]) -> dict[str, float | int]:
    results_list = list(results)
    total = len(results_list)
    return {
        "total": total,
        "attack_success": sum(1 for r in results_list if r.attack_success),
        "task_success": sum(1 for r in results_list if r.task_success),
        "average_steps": mean(r.steps for r in results_list) if total else 0.0,
    }


def main() -> None:
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for idx in range(NUM_EPISODES):
        episode_result, _ = _run_single_demo_episode(
            topology=TOPOLOGY, defense_profile="none", dataset_path=OUTPUT_JSONL
        )
        results.append(episode_result)
        print(f"Completed episode {idx + 1}/{NUM_EPISODES}")

    counts = _aggregate_counts(results)

    print("\nSmoke batch demo summary:")
    print(f"  total_episodes: {counts['total']}")
    print(f"  attack_success_true: {counts['attack_success']}")
    print(f"  task_success_true: {counts['task_success']}")
    print(f"  average_steps: {counts['average_steps']:.2f}")
    print(f"  dataset_path: {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
