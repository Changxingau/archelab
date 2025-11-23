"""Simple plotting utilities for Archelab/Kiro MAS metrics."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd

from analysis.compute_metrics import compute_metrics


_LOGGER = logging.getLogger(__name__)


def _save_figure(fig: plt.Figure, output_path: Optional[str]) -> None:
    if output_path is None:
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")


def plot_attack_success_by_attacker_profile(
    jsonl_path: str,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot attack_success_rate grouped by attacker_profile.

    If output_path is provided, save the figure to that path.
    Returns the matplotlib Figure for further use.
    """

    metrics = compute_metrics(jsonl_path, groupby_levels=["attacker_profile"])

    fig, ax = plt.subplots()

    attacker_profiles = metrics["attacker_profile"].astype(str)
    ax.bar(attacker_profiles, metrics["attack_success_rate"])

    ax.set_xlabel("attacker_profile")
    ax.set_ylabel("attack_success_rate")
    ax.set_title("Attack Success Rate by Attacker Profile")
    ax.set_xticks(range(len(attacker_profiles)))
    ax.set_xticklabels(attacker_profiles, rotation=45, ha="right")

    _save_figure(fig, output_path)

    return fig


def plot_archetype_risk_profile(
    jsonl_path: str,
    groupby_levels: Optional[Sequence[str]] = None,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot a comparative bar chart for behavior_archetype risk.

    Default grouping is ["behavior_archetype"]. For each archetype,
    show attack_success_rate, contains_secret_in_msg_rate, and
    unauthorized_write_rate side by side.
    """

    if groupby_levels is None:
        groupby_levels = ["behavior_archetype"]

    metrics = compute_metrics(jsonl_path, groupby_levels=groupby_levels)

    fig, ax = plt.subplots()

    labels = metrics[groupby_levels].astype(str).agg(" | ".join, axis=1)
    x = pd.Index(range(len(labels)))
    width = 0.25

    ax.bar(x - width, metrics["attack_success_rate"], width, label="attack_success_rate")
    ax.bar(
        x,
        metrics["contains_secret_in_msg_rate"],
        width,
        label="contains_secret_in_msg_rate",
    )
    ax.bar(x + width, metrics["unauthorized_write_rate"], width, label="unauthorized_write_rate")

    ax.set_xlabel(" | ".join(groupby_levels))
    ax.set_ylabel("Rate")
    ax.set_title("Behavior Archetype Risk Profile")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()

    _save_figure(fig, output_path)

    return fig


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MAS metric plots from JSONL episodes.")
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file.")
    parser.add_argument(
        "--output-dir",
        default=Path("analysis/outputs"),
        type=Path,
        help="Directory to write plots to (default: analysis/outputs).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    args = _parse_args(argv)

    output_dir = args.output_dir
    attack_success_path = output_dir / "attack_success_by_attacker_profile.png"
    archetype_risk_path = output_dir / "behavior_archetype_risk_profile.png"

    _LOGGER.info("Generating attack success plot at %s", attack_success_path)
    plot_attack_success_by_attacker_profile(args.jsonl_path, output_path=str(attack_success_path))

    _LOGGER.info("Generating behavior archetype risk plot at %s", archetype_risk_path)
    plot_archetype_risk_profile(args.jsonl_path, output_path=str(archetype_risk_path))


if __name__ == "__main__":
    main()
