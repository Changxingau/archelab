"""Compute MAS security metrics from Archelab/Kiro JSONL episodes."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

from archelab.analysis.load_dataset import load_episodes

_LOGGER = logging.getLogger(__name__)


DEFAULT_GROUPBY_LEVELS = [
    "attacker_profile",
    "behavior_archetype",
    "topology",
]


def compute_metrics(
    jsonl_path: str,
    groupby_levels: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Load episodes from a JSONL file and compute core MAS security metrics.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL episodes file.
    groupby_levels: Optional[Sequence[str]]
        Columns to group by when aggregating metrics. Defaults to
        ``["attacker_profile", "behavior_archetype", "topology"]``.

    Returns
    -------
    pd.DataFrame
        Aggregated metrics for each group.
    """

    if groupby_levels is None:
        groupby_levels = DEFAULT_GROUPBY_LEVELS

    episodes = load_episodes(jsonl_path)
    grouped = episodes.groupby(groupby_levels, dropna=False)

    metrics = grouped.agg(
        attack_success_rate=("attack_success", "mean"),
        contains_secret_in_msg_rate=("contains_secret_in_msg", "mean"),
        unauthorized_write_rate=("unauthorized_write", "mean"),
        task_success_rate=("task_success", "mean"),
        episode_count=("episode_id", "count"),
    ).reset_index()

    return metrics


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute core MAS security metrics from Archelab/Kiro JSONL episodes.",
    )
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file.")
    parser.add_argument(
        "--output-csv",
        nargs="?",
        const="analysis/outputs/metrics.csv",
        default=None,
        help=(
            "Optional path to write metrics CSV (default: analysis/outputs/metrics.csv) "
            "when flag is provided."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = _parse_args(argv)

    metrics = compute_metrics(args.jsonl_path)
    print(metrics.to_string(index=False))

    total_episodes = int(metrics["episode_count"].sum()) if not metrics.empty else 0
    print(f"\nComputed metrics for {len(metrics)} group(s) spanning {total_episodes} episode(s).")

    if args.output_csv:
        output_path = Path(args.output_csv)
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
        metrics.to_csv(output_path, index=False)
        _LOGGER.info("Wrote metrics to %s", output_path)


if __name__ == "__main__":
    main()
