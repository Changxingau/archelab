"""Run multiple demo MAS episodes and build a small dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Optional

from archelab.episodes.kiro_demo_flow import run_demo_episode
from archelab.logging_utils.dataset_writer import write_episodes_csv
from archelab.models.episode_result import EpisodeResult


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic Kiro demo flow multiple times and export a "
            "JSONL/CSV dataset for ArcheLab benchmarking."
        )
    )
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=50,
        help="Number of demo episodes to run (default: 50).",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("demo_data/batch_episodes.jsonl"),
        help="Path to the output JSONL dataset (default: demo_data/batch_episodes.jsonl).",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path("demo_data/batch_episodes.csv"),
        help="Optional path to export CSV stats (default: demo_data/batch_episodes.csv).",
    )
    parser.add_argument(
        "--topology",
        type=str,
        default="insecure",
        help="Topology label to tag each episode (default: insecure).",
    )
    parser.add_argument(
        "--defense-profile",
        type=str,
        default="none",
        help="Defense profile name to store in episode metadata (default: none).",
    )
    return parser.parse_args()


def _ensure_output_dirs(dataset_path: Path, csv_path: Optional[Path]) -> None:
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)


def _rate(results: Iterable[EpisodeResult], predicate) -> float:
    items = list(results)
    total = len(items)
    if total == 0:
        return 0.0
    return sum(1 for item in items if predicate(item)) / total


def _summarize_results(results: List[EpisodeResult]) -> dict:
    return {
        "total_episodes": len(results),
        "task_success_rate": _rate(results, lambda r: r.task_success),
        "attack_success_rate": _rate(results, lambda r: r.attack_success),
        "leakage_rate": _rate(results, lambda r: r.contains_secret_in_msg),
        "unauthorized_write_rate": _rate(results, lambda r: bool(r.unauthorized_write)),
        "average_steps": mean([r.steps for r in results]) if results else 0.0,
    }


def run_batch_demo(
    num_episodes: int = 50,
    dataset_path: Path | str = Path("demo_data/batch_episodes.jsonl"),
    csv_path: Path | str | None = Path("demo_data/batch_episodes.csv"),
    topology: str = "insecure",
    defense_profile: str | None = "none",
    progress_interval: int = 10,
    verbose_episodes: bool = False,
) -> List[EpisodeResult]:
    """Run multiple demo episodes and export the dataset."""

    dataset_path = Path(dataset_path)
    csv_path = Path(csv_path) if csv_path is not None else None

    _ensure_output_dirs(dataset_path, csv_path)

    results: List[EpisodeResult] = []

    for idx in range(num_episodes):
        episode_result, _ = run_demo_episode(
            topology=topology,
            defense_profile=defense_profile,
            dataset_path=dataset_path,
            verbose=verbose_episodes,
        )
        results.append(episode_result)

        if progress_interval and (idx + 1) % progress_interval == 0:
            print(f"Completed {idx + 1}/{num_episodes} episodes")

    if csv_path is not None:
        write_episodes_csv(csv_path, results)

    summary = _summarize_results(results)
    print("Batch demo summary:")
    for key, value in summary.items():
        if key.endswith("rate"):
            print(f"  {key}: {value:.2%}")
        elif key == "average_steps":
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    return results


def main() -> None:
    args = _parse_args()

    run_batch_demo(
        num_episodes=args.num_episodes,
        dataset_path=args.dataset_path,
        csv_path=args.csv_path,
        topology=args.topology,
        defense_profile=args.defense_profile,
    )


if __name__ == "__main__":
    main()
