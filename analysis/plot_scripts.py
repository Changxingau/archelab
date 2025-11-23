"""Plotting helpers for Archelab/Kiro MAS security metrics."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt

from analysis.compute_metrics import compute_metrics

_LOGGER = logging.getLogger(__name__)


DEFAULT_OUTPUT_DIR = Path("analysis/outputs")


def plot_attack_success_by_attacker_profile(
    jsonl_path: str,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot ``attack_success_rate`` grouped by ``attacker_profile``.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL dataset file.
    output_path: Optional[str]
        Optional path to save the plot image. When provided, the parent
        directories are created automatically.

    Returns
    -------
    plt.Figure
        The matplotlib figure containing the plot.
    """

    metrics = compute_metrics(jsonl_path, groupby_levels=["attacker_profile"])

    fig, ax = plt.subplots()
    x_positions = range(len(metrics))
    ax.bar(x_positions, metrics["attack_success_rate"], color="C0")
    ax.set_xlabel("Attacker Profile")
    ax.set_ylabel("Attack Success Rate")
    ax.set_title("Attack Success Rate by Attacker Profile")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(metrics["attacker_profile"], rotation=45, ha="right")
    ax.set_ylim(0, 1)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_file, bbox_inches="tight")
        _LOGGER.info("Saved attacker profile plot to %s", output_file)

    return fig


def plot_archetype_risk_profile(
    jsonl_path: str,
    groupby_levels: Optional[Sequence[str]] = None,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot a comparative bar chart for behavior archetype risk metrics.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL dataset file.
    groupby_levels: Optional[Sequence[str]]
        Columns to group by when aggregating metrics. Defaults to
        ``["behavior_archetype"]``.
    output_path: Optional[str]
        Optional path to save the plot image. When provided, the parent
        directories are created automatically.

    Returns
    -------
    plt.Figure
        The matplotlib figure containing the plot.
    """

    if groupby_levels is None:
        groupby_levels = ["behavior_archetype"]

    metrics = compute_metrics(jsonl_path, groupby_levels=groupby_levels)

    labels = metrics[groupby_levels].astype(str).agg(" | ".join, axis=1)
    x_positions = range(len(metrics))
    bar_width = 0.25

    fig, ax = plt.subplots()

    attack_positions = [x - bar_width for x in x_positions]
    contains_positions = list(x_positions)
    unauthorized_positions = [x + bar_width for x in x_positions]

    ax.bar(
        attack_positions,
        metrics["attack_success_rate"],
        width=bar_width,
        label="Attack Success",
        color="C0",
    )
    ax.bar(
        contains_positions,
        metrics["contains_secret_in_msg_rate"],
        width=bar_width,
        label="Contains Secret in Msg",
        color="C1",
    )
    ax.bar(
        unauthorized_positions,
        metrics["unauthorized_write_rate"],
        width=bar_width,
        label="Unauthorized Write",
        color="C2",
    )

    ax.set_xlabel(" | ".join(groupby_levels).title())
    ax.set_ylabel("Rate")
    ax.set_title("Behavior Archetype Risk Profile")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0, 1)
    ax.legend()

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_file, bbox_inches="tight")
        _LOGGER.info("Saved behavior archetype risk plot to %s", output_file)

    return fig


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot Archelab/Kiro MAS security metrics.")
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file.")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory to write plot images. Default: analysis/outputs. "
            "Files are named attack_success_by_attacker_profile.png and "
            "behavior_archetype_risk_profile.png."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = _parse_args(argv)

    output_dir = Path(args.output_dir)

    plot_attack_success_by_attacker_profile(
        args.jsonl_path, output_dir / "attack_success_by_attacker_profile.png"
    )
    plot_archetype_risk_profile(
        args.jsonl_path, output_path=output_dir / "behavior_archetype_risk_profile.png"
    )


if __name__ == "__main__":
    main()
