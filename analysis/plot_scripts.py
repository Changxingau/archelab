"""Plotting helpers for Archelab/Kiro MAS security metrics."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt

from analysis.compute_metrics import compute_metrics


_LOGGER = logging.getLogger(__name__)


DEFAULT_ARCHETYPE_GROUPBY = ["behavior_archetype"]


def _ensure_output_dir(output_path: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_attack_success_by_attacker_profile(
    jsonl_path: str,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot ``attack_success_rate`` grouped by ``attacker_profile``.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL episodes file.
    output_path: Optional[str]
        Optional path to save the generated figure.

    Returns
    -------
    plt.Figure
        The matplotlib figure containing the plot.
    """

    metrics = compute_metrics(jsonl_path, groupby_levels=["attacker_profile"])

    fig, ax = plt.subplots(figsize=(8, 5))

    attacker_profiles = metrics["attacker_profile"].astype(str)
    ax.bar(attacker_profiles, metrics["attack_success_rate"])

    ax.set_xlabel("Attacker Profile")
    ax.set_ylabel("Attack Success Rate")
    ax.set_title("Attack Success Rate by Attacker Profile")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()

    if output_path:
        output_file = _ensure_output_dir(output_path)
        fig.savefig(output_file, bbox_inches="tight")
        _LOGGER.info("Saved attack success plot to %s", output_file)

    return fig


def plot_archetype_risk_profile(
    jsonl_path: str,
    groupby_levels: Optional[Sequence[str]] = None,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot a comparative bar chart for behavior archetype risk metrics.

    Default grouping is ``["behavior_archetype"]``. For each archetype (or
    group), the chart shows ``attack_success_rate``, ``contains_secret_in_msg_rate``,
    and ``unauthorized_write_rate`` side by side.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL episodes file.
    groupby_levels: Optional[Sequence[str]]
        Columns to group by when aggregating metrics. Defaults to
        ``["behavior_archetype"]``.
    output_path: Optional[str]
        Optional path to save the generated figure.

    Returns
    -------
    plt.Figure
        The matplotlib figure containing the plot.
    """

    if groupby_levels is None:
        groupby_levels = DEFAULT_ARCHETYPE_GROUPBY

    metrics = compute_metrics(jsonl_path, groupby_levels=groupby_levels)

    fig, ax = plt.subplots(figsize=(10, 6))

    labels = metrics[groupby_levels].astype(str).agg(" / ".join, axis=1)
    x = range(len(metrics))
    width = 0.25

    ax.bar([i - width for i in x], metrics["attack_success_rate"], width=width, label="Attack Success")
    ax.bar(x, metrics["contains_secret_in_msg_rate"], width=width, label="Contains Secret in Msg")
    ax.bar([i + width for i in x], metrics["unauthorized_write_rate"], width=width, label="Unauthorized Write")

    ax.set_xlabel(" / ".join(groupby_levels).title())
    ax.set_ylabel("Rate")
    ax.set_title("Behavior Archetype Risk Profile")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylim(0, 1)
    ax.legend()

    fig.tight_layout()

    if output_path:
        output_file = _ensure_output_dir(output_path)
        fig.savefig(output_file, bbox_inches="tight")
        _LOGGER.info("Saved archetype risk plot to %s", output_file)

    return fig


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate MAS security metric plots (attack success by attacker profile and "
            "behavior archetype risk profile)."
        )
    )
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file.")
    parser.add_argument(
        "--attack-success-path",
        default="analysis/outputs/attack_success_by_attacker_profile.png",
        help="Path to save the attack success plot.",
    )
    parser.add_argument(
        "--archetype-risk-path",
        default="analysis/outputs/behavior_archetype_risk_profile.png",
        help="Path to save the behavior archetype risk plot.",
    )
    parser.add_argument(
        "--groupby-levels",
        nargs="*",
        default=None,
        help=(
            "Optional grouping columns for the archetype risk plot. Defaults to "
            "['behavior_archetype'] when not provided."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = _parse_args(argv)

    plot_attack_success_by_attacker_profile(args.jsonl_path, args.attack_success_path)
    plot_archetype_risk_profile(
        args.jsonl_path,
        groupby_levels=args.groupby_levels if args.groupby_levels else None,
        output_path=args.archetype_risk_path,
    )


if __name__ == "__main__":
    main()
