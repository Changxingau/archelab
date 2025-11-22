"""Step 3.0 – Demo dataset smoke test for ArcheRisk pipeline.

This script provides a lightweight sanity check for the demo datasets produced
by ``scripts/demo_dataset.py``. It is intended to validate the basic security
metric distribution before integrating with Kiro in later steps.
"""

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, Iterable, List, Optional


BOOLEAN_KEYS = [
    "task_success",
    "attack_success",
    "contains_secret_in_msg",
    "unauthorized_write",
]


def warn(message: str) -> None:
    """Print a warning message to stderr."""

    print(f"[warn] {message}", file=sys.stderr)


def load_episodes(path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load episodes from a JSONL file.

    Parameters
    ----------
    path: str
        Path to the JSONL file containing episode payloads.
    limit: Optional[int]
        Maximum number of episodes to load; if None, load all.
    """

    if not os.path.exists(path):
        print(f"[error] Input file not found: {path}", file=sys.stderr)
        sys.exit(1)

    episodes: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            if limit is not None and len(episodes) >= limit:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    warn(f"Line {idx} is not a JSON object; skipping.")
                    continue
                episodes.append(payload)
            except json.JSONDecodeError as err:
                warn(f"Failed to parse line {idx}: {err}")
                continue

    if not episodes:
        print(f"[error] No episodes loaded from {path}; file may be empty or invalid.", file=sys.stderr)
        sys.exit(1)

    return episodes


def compute_boolean_stats(episodes: Iterable[Dict[str, Any]], key: str) -> Dict[str, Any]:
    true_count = 0
    false_count = 0
    missing = 0

    for idx, ep in enumerate(episodes):
        if key not in ep:
            missing += 1
            warn(f"Episode {idx} missing '{key}'; skipping for stats.")
            continue
        value = ep[key]
        if isinstance(value, bool):
            true_count += int(value)
            false_count += int(not value)
        else:
            missing += 1
            warn(f"Episode {idx} has non-boolean '{key}'={value!r}; skipping for stats.")

    total = true_count + false_count
    ratio = true_count / total if total else 0.0
    return {
        "true": true_count,
        "false": false_count,
        "missing": missing,
        "true_ratio": ratio,
    }


def compute_steps_stats(episodes: Iterable[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    steps: List[float] = []
    for idx, ep in enumerate(episodes):
        if "steps" not in ep:
            warn(f"Episode {idx} missing 'steps'; skipping for stats.")
            continue
        value = ep["steps"]
        if isinstance(value, (int, float)):
            steps.append(float(value))
        else:
            warn(f"Episode {idx} has non-numeric 'steps'={value!r}; skipping for stats.")

    if not steps:
        warn("No valid 'steps' values found; skipping step statistics.")
        return None

    mean_steps = statistics.mean(steps)
    return {
        "min": min(steps),
        "max": max(steps),
        "mean": mean_steps,
    }


def print_boolean_summary(key: str, stats: Dict[str, Any]) -> None:
    print(f"{key}:")
    print(f"  true: {stats['true']}")
    print(f"  false: {stats['false']}")
    if stats.get("missing"):
        print(f"  missing: {stats['missing']}")
    print(f"  true_ratio: {stats['true_ratio']:.2f}\n")


def print_preview(episodes: List[Dict[str, Any]], show_head: int) -> None:
    print(f"[Preview: first {show_head} episodes]")
    for idx, ep in enumerate(episodes[:show_head]):
        task_success = ep.get("task_success")
        attack_success = ep.get("attack_success")
        steps = ep.get("steps")
        print(
            f"Episode {idx}: task_success={task_success}, "
            f"attack_success={attack_success}, steps={steps}"
        )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a demo JSONL dataset for basic sanity checks."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the JSONL file containing episodes.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of episodes to load (default: all).",
    )
    parser.add_argument(
        "--show-head",
        type=int,
        default=3,
        help="Number of episodes to preview (default: 3).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    episodes = load_episodes(args.input, args.limit)
    total = len(episodes)
    print(f"Loaded {total} episodes from {args.input}\n")

    print("[Boolean metrics]")
    for key in BOOLEAN_KEYS:
        stats = compute_boolean_stats(episodes, key)
        print_boolean_summary(key, stats)

    step_stats = compute_steps_stats(episodes)
    if step_stats:
        print("[Steps]")
        print(f"min_steps: {int(step_stats['min']) if step_stats['min'].is_integer() else step_stats['min']}")
        print(f"max_steps: {int(step_stats['max']) if step_stats['max'].is_integer() else step_stats['max']}")
        print(f"mean_steps: {step_stats['mean']:.2f}\n")

    show_head = max(args.show_head, 0)
    if show_head:
        print_preview(episodes, show_head)


if __name__ == "__main__":
    main()
