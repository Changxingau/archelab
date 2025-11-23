"""Utilities for loading Archelab/Kiro JSONL datasets into pandas."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


_LOGGER = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "episode_id",
    "attacker_profile",
    "behavior_archetype",
    "topology",
    "defense_profile",
    "task_success",
    "attack_success",
    "unauthorized_write",
    "contains_secret_in_msg",
    "steps",
    "extra_metadata",
]


def _extract_steps(entry: Dict[str, Any]) -> Optional[int]:
    """Return the number of steps for the given episode entry."""

    if "steps" in entry:
        return entry.get("steps")

    trace = entry.get("trace")
    if isinstance(trace, dict):
        messages = trace.get("messages", [])
        if isinstance(messages, list):
            return len(messages)
    return None


def _normalize_episode(entry: dict) -> dict:
    """
    Flatten one episode entry into a normalized record.
    Apply consistent extraction rules for required MAS security fields.
    Compatible with older schema versions (meta vs extra_metadata).
    """

    record: Dict[str, Any] = {
        "episode_id": entry.get("episode_id"),
        "attacker_profile": entry.get("attacker_profile"),
        "behavior_archetype": entry.get("behavior_archetype"),
        "topology": entry.get("topology"),
        "defense_profile": entry.get("defense_profile"),
        "task_success": entry.get("task_success"),
        "attack_success": entry.get("attack_success"),
        "unauthorized_write": entry.get("unauthorized_write"),
        "contains_secret_in_msg": entry.get("contains_secret_in_msg"),
        "steps": _extract_steps(entry),
        "extra_metadata": entry.get("extra_metadata") or entry.get("meta"),
    }

    # Preserve any additional top-level fields for future exploration.
    for key, value in entry.items():
        record.setdefault(key, value)

    return record


def load_episodes(jsonl_path: str) -> pd.DataFrame:
    """Load Archelab/Kiro JSONL episodes into a flat pandas DataFrame.

    Each line is a JSON object (EpisodeResult + trace/meta). This function
    extracts the key MAS security fields and returns one row per episode.
    """

    path = Path(jsonl_path)
    records: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as fh:
        for line_num, line in enumerate(fh, start=1):
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                _LOGGER.warning("Skipping invalid JSON on line %s in %s", line_num, path)
                continue

            records.append(_normalize_episode(entry))

    df = pd.DataFrame(records)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[REQUIRED_COLUMNS + [c for c in df.columns if c not in REQUIRED_COLUMNS]]


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    parser = argparse.ArgumentParser(description="Load Archelab/Kiro JSONL episodes.")
    parser.add_argument("jsonl_path", help="Path to the JSONL dataset file")
    args = parser.parse_args()

    dataframe = load_episodes(args.jsonl_path)

    print("DataFrame head:\n", dataframe.head())
    if "attacker_profile" in dataframe.columns:
        print("\nattacker_profile counts:\n", dataframe["attacker_profile"].value_counts())
