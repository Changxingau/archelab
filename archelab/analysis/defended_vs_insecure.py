"""Phase 5.3 analysis for ArcheRisk: insecure vs defended comparisons."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from archelab.analysis.load_dataset import load_dataset

REQUIRED_COLUMNS = [
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


def _prepare_dataframe(
    records: list[dict[str, object]],
    defaults: dict[str, object],
    overrides: dict[str, object] | None = None,
) -> pd.DataFrame:
    """Create a dataframe from episode records and ensure required columns exist."""

    df = pd.DataFrame(records)
    overrides = overrides or {}

    for column in REQUIRED_COLUMNS:
        if column in overrides:
            df[column] = overrides[column]
            continue

        default_value = defaults.get(column)
        if column not in df.columns:
            df[column] = default_value
        else:
            df[column] = df[column].fillna(default_value)

    return df[REQUIRED_COLUMNS + [c for c in df.columns if c not in REQUIRED_COLUMNS]]


def load_combined(insecure_path: str, defended_path: str) -> pd.DataFrame:
    """Load insecure and defended datasets and combine them into one dataframe."""

    insecure_records = load_dataset(insecure_path)
    defended_records = load_dataset(defended_path)

    insecure_defaults: dict[str, object] = {
        "topology": "insecure",
        "defense_enabled": False,
        "defense_profile": "none",
        "defense_redacted_leaks": 0,
        "defense_blocked_writes": 0,
        "defense_generic_refusals": 0,
    }
    defended_defaults: dict[str, object] = {
        "topology": "defended",
        "defense_enabled": True,
        "defense_profile": "minimal_v1",
        "defense_redacted_leaks": 0,
        "defense_blocked_writes": 0,
        "defense_generic_refusals": 0,
    }

    insecure_overrides = {
        "topology": "insecure",
        "defense_enabled": False,
        "defense_profile": "none",
    }
    defended_overrides = {
        "topology": "defended",
        "defense_enabled": True,
    }

    insecure_df = _prepare_dataframe(
        insecure_records, insecure_defaults, overrides=insecure_overrides
    )
    defended_df = _prepare_dataframe(
        defended_records, defended_defaults, overrides=defended_overrides
    )

    combined_df = pd.concat([insecure_df, defended_df], ignore_index=True)
    return combined_df


def _mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.mean())


def compute_profile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregated statistics per attacker profile and topology."""

    grouped = df.groupby(["attacker_profile", "topology"], dropna=False)
    stats = grouped.agg(
        n_episodes=("attack_success", "size"),
        attack_success_rate=("attack_success", _mean),
        leak_rate=("contains_secret_in_msg", _mean),
        unauthorized_write_rate=("unauthorized_write", _mean),
        task_success_rate=("task_success", _mean),
    )
    return stats.reset_index()


def plot_metric_bar(stats_df: pd.DataFrame, metric: str, output_path: str) -> None:
    """Plot a metric comparing insecure vs defended per attacker profile."""

    pivot = stats_df.pivot(index="attacker_profile", columns="topology", values=metric)
    column_order = [col for col in ["insecure", "defended"] if col in pivot.columns]
    pivot = pivot[column_order]

    fig, ax = plt.subplots(figsize=(10, 6))
    pivot.plot(kind="bar", ax=ax)
    ax.set_xlabel("Attacker Profile")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.legend(title="Topology")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_attack_success(stats_df: pd.DataFrame, output_path: str) -> None:
    plot_metric_bar(stats_df, "attack_success_rate", output_path)


def plot_leak_rate(stats_df: pd.DataFrame, output_path: str) -> None:
    plot_metric_bar(stats_df, "leak_rate", output_path)


def plot_unauthorized_write(stats_df: pd.DataFrame, output_path: str) -> None:
    plot_metric_bar(stats_df, "unauthorized_write_rate", output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare insecure vs defended datasets by attacker profile."
    )
    parser.add_argument("--insecure", required=True, help="Path to insecure JSONL file")
    parser.add_argument("--defended", required=True, help="Path to defended JSONL file")
    parser.add_argument("--outdir", required=True, help="Output directory for plots")

    args = parser.parse_args()

    output_dir = Path(args.outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_df = load_combined(args.insecure, args.defended)
    stats_df = compute_profile_stats(combined_df)

    sorted_stats = stats_df.sort_values(["attacker_profile", "topology"])
    print(sorted_stats)

    stats_path = output_dir / "profile_stats.csv"
    sorted_stats.to_csv(stats_path, index=False)

    plot_attack_success(stats_df, str(output_dir / "attack_success_insecure_vs_defended.png"))
    plot_leak_rate(stats_df, str(output_dir / "leak_rate_insecure_vs_defended.png"))
    plot_unauthorized_write(
        stats_df, str(output_dir / "unauthorized_write_insecure_vs_defended.png")
    )
