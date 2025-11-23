"""Plotting helpers for Archelab/Kiro MAS security metrics."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.compute_metrics import compute_metrics

_LOGGER = logging.getLogger(__name__)


def plot_attack_success_by_attacker_profile(
    jsonl_path: str,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot attack success rates grouped by attacker profile.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL dataset file.
    output_path: Optional[str]
        Optional path to save the generated figure.

    Returns
    -------
    plt.Figure
        The created matplotlib figure.
    """

    metrics = compute_metrics(jsonl_path, groupby_levels=["attacker_profile"])

    fig, ax = plt.subplots()
    ax.bar(metrics["attacker_profile"], metrics["attack_success_rate"])
    ax.set_xlabel("Attacker Profile")
    ax.set_ylabel("Attack Success Rate")
    ax.set_title("Attack Success Rate by Attacker Profile")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, bbox_inches="tight")
        _LOGGER.info("Saved attack success plot to %s", output)

    return fig


def plot_archetype_risk_profile(
    jsonl_path: str,
    groupby_levels: Optional[Sequence[str]] = None,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot a grouped bar chart for archetype risk metrics.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL dataset file.
    groupby_levels: Optional[Sequence[str]]
        Columns to group by when aggregating metrics. Defaults to
        ``["behavior_archetype"]``.
    output_path: Optional[str]
        Optional path to save the generated figure.

    Returns
    -------
    plt.Figure
        The created matplotlib figure.
    """

    if groupby_levels is None:
        groupby_levels = ["behavior_archetype"]

    metrics = compute_metrics(jsonl_path, groupby_levels=groupby_levels)

    archetypes = metrics["behavior_archetype"].astype(str)
    x = np.arange(len(archetypes))
    width = 0.25

    fig, ax = plt.subplots()

    ax.bar(x - width, metrics["attack_success_rate"], width, label="Attack Success")
    ax.bar(
        x,
        metrics["contains_secret_in_msg_rate"],
        width,
        label="Contains Secret in Msg",
    )
    ax.bar(
        x + width,
        metrics["unauthorized_write_rate"],
        width,
        label="Unauthorized Write",
    )

    ax.set_xlabel("Behavior Archetype")
    ax.set_ylabel("Rate")
    ax.set_title("Behavior Archetype Risk Profile")
    ax.set_xticks(x)
    ax.set_xticklabels(archetypes, rotation=45, ha="right")
    ax.legend()

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, bbox_inches="tight")
        _LOGGER.info("Saved archetype risk profile plot to %s", output)

    return fig


def _main(jsonl_path: str) -> None:
    """Generate default plots for the provided dataset path."""

    plot_attack_success_by_attacker_profile(
        jsonl_path, output_path="analysis/outputs/attack_success_by_attacker_profile.png"
    )
    plot_archetype_risk_profile(
        jsonl_path, output_path="analysis/outputs/behavior_archetype_risk_profile.png"
    )


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    parser = argparse.ArgumentParser(description="Plot MAS security metrics from JSONL episodes.")
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file.")
    args = parser.parse_args()

    _main(args.jsonl_path)
