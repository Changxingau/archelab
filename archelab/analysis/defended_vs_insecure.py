"""Compare defended vs insecure datasets and generate plots."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import pandas as pd

from archelab.analysis.load_dataset import load_episodes

__all__ = [
    "load_combined",
    "compute_profile_stats",
    "plot_attack_success",
    "plot_leak_rate",
    "plot_unauthorized_write",
]


_REQUIRED_COLUMNS: List[str] = [
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


_DEFENDED_DEFAULTS = {
    "topology": "defended",
    "defense_enabled": True,
    "defense_profile": "none",
    "defense_redacted_leaks": 0,
    "defense_blocked_writes": 0,
    "defense_generic_refusals": 0,
}


_INSECURE_DEFAULTS = {
    "topology": "insecure",
    "defense_enabled": False,
    "defense_profile": "none",
    "defense_redacted_leaks": 0,
    "defense_blocked_writes": 0,
    "defense_generic_refusals": 0,
}


def _ensure_columns(df: pd.DataFrame, defaults: dict) -> pd.DataFrame:
    """Ensure the DataFrame contains all required columns with defaults."""

    for column in _REQUIRED_COLUMNS:
        if column not in df.columns:
            default_value = defaults.get(column)
            df[column] = default_value
    return df[_REQUIRED_COLUMNS + [c for c in df.columns if c not in _REQUIRED_COLUMNS]]


def load_combined(insecure_path: str, defended_path: str) -> pd.DataFrame:
    """Load insecure and defended datasets and combine into one DataFrame."""

    insecure_df = load_episodes(insecure_path)
    defended_df = load_episodes(defended_path)

    insecure_df = _ensure_columns(insecure_df, _INSECURE_DEFAULTS)
    defended_df = _ensure_columns(defended_df, _DEFENDED_DEFAULTS)

    return pd.concat([insecure_df, defended_df], ignore_index=True, sort=False)


def compute_profile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-attacker profile stats for each topology."""

    # Ensure boolean columns are numeric for mean calculation
    bool_columns: Iterable[str] = [
        "attack_success",
        "contains_secret_in_msg",
        "unauthorized_write",
        "task_success",
    ]
    df = df.copy()
    for column in bool_columns:
        if column in df.columns:
            df[column] = df[column].astype(float)

    grouped = (
        df.groupby(["attacker_profile", "topology"], dropna=False)[
            [
                "attack_success",
                "contains_secret_in_msg",
                "unauthorized_write",
                "task_success",
            ]
        ]
        .mean()
        .reset_index()
    )

    grouped = grouped.rename(
        columns={
            "attack_success": "attack_success_rate",
            "contains_secret_in_msg": "leak_rate",
            "unauthorized_write": "unauthorized_write_rate",
            "task_success": "task_success_rate",
        }
    )

    return grouped


def _plot_rate(stats_df: pd.DataFrame, rate_column: str, ylabel: str, title: str, output_path: Path) -> None:
    """Generic helper to plot rates for insecure vs defended topologies."""

    pivot_df = stats_df.pivot(
        index="attacker_profile", columns="topology", values=rate_column
    ).fillna(0)

    attacker_profiles = list(pivot_df.index)
    topologies = ["insecure", "defended"]
    bar_width = 0.35
    x = range(len(attacker_profiles))

    fig, ax = plt.subplots(figsize=(10, 6))

    for idx, topology in enumerate(topologies):
        offsets = [i + (idx - 0.5) * bar_width for i in x]
        ax.bar(
            offsets,
            pivot_df.get(topology, pd.Series(0, index=attacker_profiles)),
            width=bar_width,
            label=topology.title(),
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(attacker_profiles, rotation=45, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.set_ylim(0, 1)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)


def plot_attack_success(stats_df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot attack success rate comparison."""

    _plot_rate(
        stats_df,
        rate_column="attack_success_rate",
        ylabel="Attack Success Rate",
        title="Attack Success Rate by Attacker Profile",
        output_path=Path(output_path),
    )


def plot_leak_rate(stats_df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot leak rate comparison."""

    _plot_rate(
        stats_df,
        rate_column="leak_rate",
        ylabel="Leak Rate",
        title="Leak Rate by Attacker Profile",
        output_path=Path(output_path),
    )


def plot_unauthorized_write(stats_df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot unauthorized write rate comparison."""

    _plot_rate(
        stats_df,
        rate_column="unauthorized_write_rate",
        ylabel="Unauthorized Write Rate",
        title="Unauthorized Write Rate by Attacker Profile",
        output_path=Path(output_path),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate defended vs insecure comparison plots."
    )
    parser.add_argument("--insecure", required=True, help="Path to insecure JSONL dataset")
    parser.add_argument("--defended", required=True, help="Path to defended JSONL dataset")
    parser.add_argument(
        "--outdir",
        required=True,
        help="Directory where output plots will be saved",
    )
    return parser.parse_args()


def _run_cli(args: argparse.Namespace) -> None:
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    combined_df = load_combined(args.insecure, args.defended)
    stats_df = compute_profile_stats(combined_df)

    plot_attack_success(stats_df, outdir / "attack_success.png")
    plot_leak_rate(stats_df, outdir / "leak_rate.png")
    plot_unauthorized_write(stats_df, outdir / "unauthorized_write.png")

    print(stats_df.to_string(index=False))


if __name__ == "__main__":
    cli_args = _parse_args()
    _run_cli(cli_args)
