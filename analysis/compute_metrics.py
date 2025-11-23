"""Compute core MAS security metrics from Archelab/Kiro JSONL episodes."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

from analysis.load_dataset import load_episodes


_LOGGER = logging.getLogger(__name__)


def compute_metrics(
    jsonl_path: str,
    groupby_levels: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Load episodes from a JSONL file and compute core MAS security metrics.

    Parameters
    ----------
    jsonl_path:
        Path to the JSONL file produced by Phase 3 scripts.
    groupby_levels:
        Columns to group by when aggregating metrics. Defaults to
        ["attacker_profile", "behavior_archetype", "topology"].

    Returns
    -------
    pd.DataFrame
        Aggregated metrics with one row per group.
    """

    if groupby_levels is None:
        groupby_levels = ["attacker_profile", "behavior_archetype", "topology"]

    df = load_episodes(jsonl_path)

    if df.empty:
        _LOGGER.warning("No episodes found in %s", jsonl_path)
        return pd.DataFrame(columns=[*groupby_levels, "attack_success_rate", "contains_secret_in_msg_rate", "unauthorized_write_rate", "task_success_rate", "episode_count"])

    grouped = df.groupby(groupby_levels, dropna=False)

    metrics = grouped.agg(
        attack_success_rate=("attack_success", "mean"),
        contains_secret_in_msg_rate=("contains_secret_in_msg", "mean"),
        unauthorized_write_rate=("unauthorized_write", "mean"),
        task_success_rate=("task_success", "mean"),
        episode_count=("episode_id", "count"),
    ).reset_index()

    return metrics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute MAS security metrics from JSONL episodes.")
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file")
    parser.add_argument(
        "--output-csv",
        dest="output_csv",
        help="Optional filename to write metrics CSV under analysis/outputs/ (or specified path)",
    )
    return parser.parse_args()


def _resolve_output_path(output_csv: str) -> Path:
    path = Path(output_csv)
    if path.parent == Path("."):
        base_dir = Path(__file__).resolve().parent / "outputs"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / path

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = _parse_args()

    metrics = compute_metrics(args.jsonl_path)

    print(metrics.to_string(index=False))
    print(f"\nTotal groups: {len(metrics)}")
    if not metrics.empty and "episode_count" in metrics.columns:
        print(f"Total episodes: {metrics['episode_count'].sum()}")

    if args.output_csv:
        output_path = _resolve_output_path(args.output_csv)
        metrics.to_csv(output_path, index=False)
        _LOGGER.info("Metrics written to %s", output_path)


if __name__ == "__main__":
    main()
