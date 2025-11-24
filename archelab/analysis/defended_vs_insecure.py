"""Analysis helpers for comparing defended vs insecure datasets."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import pandas as pd

from archelab.analysis.load_dataset import load_episodes

REQUIRED_COLUMNS: List[str] = [
    "topology",
    "attacker_profile",
    "task_success",
    "attack_success",
    "contains_secret_in_msg",
    "unauthorized_write",
    "defense_enabled",
    "defense_profile",
    "defense_redacted_leaks",
    "defense_blocked_writes",
    "defense_generic_refusals",
]


def _ensure_columns(df: pd.DataFrame, defaults: dict[str, object]) -> pd.DataFrame:
    """Ensure the dataframe has all required columns with appropriate defaults."""

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = defaults.get(column)
    return df[REQUIRED_COLUMNS + [c for c in df.columns if c not in REQUIRED_COLUMNS]]


def load_combined(insecure_path: str, defended_path: str) -> pd.DataFrame:
    """Load insecure and defended datasets and combine them into one dataframe."""

    insecure_df = load_episodes(insecure_path)
    defended_df = load_episodes(defended_path)

    insecure_defaults = {
        "topology": "insecure",
        "defense_enabled": False,
        "defense_profile": "none",
        "defense_redacted_leaks": 0,
        "defense_blocked_writes": 0,
        "defense_generic_refusals": 0,
    }
    defended_defaults = {
        "topology": "defended",
        "defense_enabled": True,
        "defense_profile": "none",
        "defense_redacted_leaks": 0,
        "defense_blocked_writes": 0,
        "defense_generic_refusals": 0,
    }

    insecure_df = _ensure_columns(insecure_df, insecure_defaults)
    defended_df = _ensure_columns(defended_df, defended_defaults)

    combined_df = pd.concat([insecure_df, defended_df], ignore_index=True)
    return combined_df


def _safe_mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.mean()) if not numeric.empty else float("nan")


def compute_profile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-profile statistics for insecure vs defended topologies."""

    grouped = df.groupby(["attacker_profile", "topology"])

    stats = grouped.apply(
        lambda group: pd.Series(
            {
                "attack_success_rate": _safe_mean(group["attack_success"]),
                "leak_rate": _safe_mean(group["contains_secret_in_msg"]),
                "unauthorized_write_rate": _safe_mean(group["unauthorized_write"]),
                "task_success_rate": _safe_mean(group["task_success"]),
            }
        )
    )

    stats = stats.reset_index()
    stats = stats.sort_values(["attacker_profile", "topology"]).reset_index(drop=True)
    return stats


def _plot_rate(
    stats_df: pd.DataFrame,
    value_column: str,
    ylabel: str,
    output_path: str | Path,
    title: str,
) -> None:
    """Plot a bar chart for the given rate column."""

    pivot = stats_df.pivot(
        index="attacker_profile", columns="topology", values=value_column
    )
    # Ensure consistent column order
    columns: Iterable[str] = [c for c in ["insecure", "defended"] if c in pivot.columns]
    pivot = pivot[columns]

    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_xlabel("Attacker Profile")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(title="Topology")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_attack_success(stats_df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot attack success rates by attacker profile."""

    _plot_rate(
        stats_df,
        value_column="attack_success_rate",
        ylabel="Attack Success Rate",
        output_path=output_path,
        title="Attack Success Rate by Attacker Profile",
    )


def plot_leak_rate(stats_df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot leak rates by attacker profile."""

    _plot_rate(
        stats_df,
        value_column="leak_rate",
        ylabel="Leak Rate",
        output_path=output_path,
        title="Leak Rate by Attacker Profile",
    )


def plot_unauthorized_write(stats_df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot unauthorized write rates by attacker profile."""

    _plot_rate(
        stats_df,
        value_column="unauthorized_write_rate",
        ylabel="Unauthorized Write Rate",
        output_path=output_path,
        title="Unauthorized Write Rate by Attacker Profile",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare defended vs insecure datasets by attacker profile."
    )
    parser.add_argument("--insecure", required=True, help="Path to insecure JSONL file")
    parser.add_argument("--defended", required=True, help="Path to defended JSONL file")
    parser.add_argument("--outdir", required=True, help="Directory to save plots")

    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    combined_df = load_combined(args.insecure, args.defended)
    stats_df = compute_profile_stats(combined_df)

    plot_attack_success(stats_df, outdir / "attack_success.png")
    plot_leak_rate(stats_df, outdir / "leak_rate.png")
    plot_unauthorized_write(stats_df, outdir / "unauthorized_write.png")

    print(stats_df)
