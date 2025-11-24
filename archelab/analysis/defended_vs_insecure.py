"""Phase 5.3 analysis for comparing defended vs insecure topologies."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from archelab.analysis.load_dataset import load_dataset

REQUIRED_COLUMNS: list[str] = [
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


def _ensure_required_columns(df: pd.DataFrame, defaults: dict[str, object]) -> pd.DataFrame:
    """Ensure the dataframe contains required columns with default values."""

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = defaults.get(column)
    return df


def _prepare_dataframe(records: list[dict[str, object]], topology: str) -> pd.DataFrame:
    """Convert records to a normalized dataframe for the given topology."""

    df = pd.DataFrame(records)
    defaults: dict[str, object]

    if topology == "insecure":
        defaults = {
            "topology": "insecure",
            "defense_enabled": False,
            "defense_profile": "none",
            "defense_redacted_leaks": 0,
            "defense_blocked_writes": 0,
            "defense_generic_refusals": 0,
        }
    else:
        defaults = {
            "topology": "defended",
            "defense_enabled": True,
            "defense_profile": "minimal_v1",
            "defense_redacted_leaks": 0,
            "defense_blocked_writes": 0,
            "defense_generic_refusals": 0,
        }

    df = _ensure_required_columns(df, defaults)
    df["topology"] = defaults["topology"]
    df["defense_enabled"] = defaults["defense_enabled"]

    defense_profile_default = defaults.get("defense_profile", "minimal_v1")
    df["defense_profile"] = df.get("defense_profile", defense_profile_default).fillna(
        defense_profile_default
    )

    for column in (
        "defense_redacted_leaks",
        "defense_blocked_writes",
        "defense_generic_refusals",
    ):
        df[column] = pd.to_numeric(df.get(column, 0), errors="coerce").fillna(0)

    return df[REQUIRED_COLUMNS + [c for c in df.columns if c not in REQUIRED_COLUMNS]]


def load_combined(insecure_path: str, defended_path: str) -> pd.DataFrame:
    """Load insecure and defended datasets and combine them into a single dataframe."""

    insecure_records = load_dataset(insecure_path)
    defended_records = load_dataset(defended_path)

    insecure_df = _prepare_dataframe(insecure_records, topology="insecure")
    defended_df = _prepare_dataframe(defended_records, topology="defended")

    combined_df = pd.concat([insecure_df, defended_df], ignore_index=True)
    return combined_df


def _safe_mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.mean()) if not numeric.empty else float("nan")


def compute_profile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-attacker profile statistics for insecure vs defended topologies."""

    grouped = df.groupby(["attacker_profile", "topology"])

    stats = grouped.agg(
        n_episodes=("attacker_profile", "size"),
        attack_success_rate=("attack_success", _safe_mean),
        leak_rate=("contains_secret_in_msg", _safe_mean),
        unauthorized_write_rate=("unauthorized_write", _safe_mean),
        task_success_rate=("task_success", _safe_mean),
    )

    return stats.reset_index()


def plot_metric_bar(stats_df: pd.DataFrame, metric: str, output_path: str) -> None:
    """Plot a bar chart comparing insecure vs defended for a metric."""

    pivot = stats_df.pivot(index="attacker_profile", columns="topology", values=metric)
    columns: Iterable[str] = [col for col in ["insecure", "defended"] if col in pivot.columns]
    pivot = pivot.reindex(columns=columns)

    attacker_profiles = list(pivot.index)
    x_indices = range(len(attacker_profiles))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    for idx, topology in enumerate(columns):
        offsets = [x + (idx - (len(columns) - 1) / 2) * width for x in x_indices]
        ax.bar(offsets, pivot[topology], width=width, label=topology)

    ax.set_xlabel("Attacker Profile")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_xticks(list(x_indices))
    ax.set_xticklabels(attacker_profiles, rotation=45, ha="right")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_attack_success(stats_df: pd.DataFrame, output_path: str) -> None:
    """Plot attack success rates by attacker profile."""

    plot_metric_bar(stats_df, metric="attack_success_rate", output_path=output_path)


def plot_leak_rate(stats_df: pd.DataFrame, output_path: str) -> None:
    """Plot leak rates by attacker profile."""

    plot_metric_bar(stats_df, metric="leak_rate", output_path=output_path)


def plot_unauthorized_write(stats_df: pd.DataFrame, output_path: str) -> None:
    """Plot unauthorized write rates by attacker profile."""

    plot_metric_bar(stats_df, metric="unauthorized_write_rate", output_path=output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare defended vs insecure datasets by attacker profile."
    )
    parser.add_argument("--insecure", required=True, help="Path to insecure JSONL file")
    parser.add_argument("--defended", required=True, help="Path to defended JSONL file")
    parser.add_argument(
        "--outdir", required=True, help="Directory to save plots and statistics"
    )

    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    combined_df = load_combined(args.insecure, args.defended)
    stats_df = compute_profile_stats(combined_df)

    print(stats_df.sort_values(["attacker_profile", "topology"]))

    stats_path = outdir / "profile_stats.csv"
    stats_df.to_csv(stats_path, index=False)

    plot_attack_success(
        stats_df, output_path=str(outdir / "attack_success_insecure_vs_defended.png")
    )
    plot_leak_rate(
        stats_df, output_path=str(outdir / "leak_rate_insecure_vs_defended.png")
    )
    plot_unauthorized_write(
        stats_df,
        output_path=str(outdir / "unauthorized_write_insecure_vs_defended.png"),
    )
