"""
Step 3.0 of the ArcheRisk pipeline.

This script provides a smoke test for demo datasets produced by
`scripts/demo_dataset.py`. It performs lightweight sanity checks on the
security metrics before Kiro integration to validate the basic metric
distribution.
"""

import argparse
import json
import sys
from collections import Counter
from statistics import mean
from typing import Any, Dict, List


BOOLEAN_METRICS = [
    "task_success",
    "attack_success",
    "contains_secret_in_msg",
    "unauthorized_write",
]


def load_episodes(path: str, limit: int | None) -> List[Dict[str, Any]]:
    episodes: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if limit is not None and idx >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    episodes.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    print(f"Warning: skipping invalid JSON line {idx}: {exc}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: input file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error: could not read file {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not episodes:
        print(f"Error: no episodes loaded from {path}. Ensure the file is not empty.", file=sys.stderr)
        sys.exit(1)

    return episodes


def compute_boolean_stats(episodes: List[Dict[str, Any]]) -> Dict[str, Counter]:
    stats: Dict[str, Counter] = {}
    for metric in BOOLEAN_METRICS:
        counter = Counter()
        for ep in episodes:
            value = ep.get(metric)
            if value is None:
                print(
                    f"Warning: episode missing '{metric}'. Treating as False for aggregation.",
                    file=sys.stderr,
                )
                value = False
            counter[bool(value)] += 1
        stats[metric] = counter
    return stats


def compute_step_stats(episodes: List[Dict[str, Any]]) -> Dict[str, float]:
    step_values: List[int] = []
    for ep in episodes:
        steps = ep.get("steps")
        if isinstance(steps, int):
            step_values.append(steps)
        else:
            print("Warning: episode missing or invalid 'steps'. Skipping.", file=sys.stderr)
    if not step_values:
        return {"min": 0, "max": 0, "mean": 0.0}
    return {
        "min": min(step_values),
        "max": max(step_values),
        "mean": mean(step_values),
    }


def print_summary(episodes: List[Dict[str, Any]], boolean_stats: Dict[str, Counter], step_stats: Dict[str, float], show_head: int) -> None:
    print(f"Loaded {len(episodes)} episodes from input file\n")
    print("[Boolean metrics]")
    for metric in BOOLEAN_METRICS:
        counter = boolean_stats.get(metric, Counter())
        true_count = counter.get(True, 0)
        false_count = counter.get(False, 0)
        total = true_count + false_count
        true_ratio = (true_count / total) if total else 0.0
        print(f"{metric}:")
        print(f"  true: {true_count}")
        print(f"  false: {false_count}")
        print(f"  true_ratio: {true_ratio:.2f}\n")

    print("[Steps]")
    print(f"min_steps: {step_stats['min']}")
    print(f"max_steps: {step_stats['max']}")
    print(f"mean_steps: {step_stats['mean']:.2f}\n")

    print(f"[Preview: first {show_head} episodes]")
    for idx, ep in enumerate(episodes[:show_head]):
        ts = ep.get("task_success")
        atk = ep.get("attack_success")
        steps = ep.get("steps")
        print(f"Episode {idx}: task_success={ts}, attack_success={atk}, steps={steps}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect demo dataset JSONL and compute simple stats.")
    parser.add_argument("--input", required=True, help="Path to the episodes JSONL file.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of episodes to load.")
    parser.add_argument("--show-head", type=int, default=3, dest="show_head", help="Number of episodes to preview.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    episodes = load_episodes(args.input, args.limit)
    boolean_stats = compute_boolean_stats(episodes)
    step_stats = compute_step_stats(episodes)
    print_summary(episodes, boolean_stats, step_stats, args.show_head)


if __name__ == "__main__":
    main()
