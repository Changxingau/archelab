"""Phase 4.1 – Load Archelab/Kiro JSONL episodes into a DataFrame.

This module provides a helper for converting JSONL benchmark episodes into a
flat ``pandas.DataFrame`` suitable for later analysis and plotting steps.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


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


def _extract_steps(payload: Dict[str, Any]) -> Optional[int]:
    """Derive the number of steps for an episode payload.

    Preference order:
    1. An explicit ``steps`` field on the payload.
    2. The number of messages inside ``trace['messages']``.

    If neither is available, returns ``None``.
    """

    if "steps" in payload:
        try:
            # Cast to int when possible while preserving None/invalid values.
            return int(payload["steps"])  # type: ignore[arg-type]
        except (TypeError, ValueError):
            logger.debug("Unable to coerce steps=%r to int; falling back to trace.", payload["steps"])

    trace = payload.get("trace")
    if isinstance(trace, dict):
        messages = trace.get("messages", [])
        if isinstance(messages, list):
            return len(messages)

    return None


def _normalize_episode(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten an episode payload into a dictionary row for pandas."""

    row: Dict[str, Any] = dict(payload)

    row["episode_id"] = payload.get("episode_id")
    row["attacker_profile"] = payload.get("attacker_profile")
    row["behavior_archetype"] = payload.get("behavior_archetype")
    row["topology"] = payload.get("topology")
    row["defense_profile"] = payload.get("defense_profile")
    row["task_success"] = payload.get("task_success")
    row["attack_success"] = payload.get("attack_success")
    row["unauthorized_write"] = payload.get("unauthorized_write")
    row["contains_secret_in_msg"] = payload.get("contains_secret_in_msg")
    row["steps"] = _extract_steps(payload)
    row["extra_metadata"] = payload.get("extra_metadata")

    return row


def load_episodes(jsonl_path: str) -> pd.DataFrame:
    """Load Archelab/Kiro JSONL episodes into a flat pandas DataFrame.

    Each line is expected to be a JSON object representing an episode result.
    Fields of interest are normalized into explicit columns while retaining any
    additional metadata that may be present.

    Parameters
    ----------
    jsonl_path: str
        Path to the JSONL file to load.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing one row per episode with the required columns.
    """

    path = Path(jsonl_path)
    rows: List[Dict[str, Any]] = []

    if not path.exists():
        logger.warning("Input JSONL file not found: %s", jsonl_path)
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as err:
                logger.warning("Skipping line %d in %s due to JSON error: %s", idx, jsonl_path, err)
                continue

            if not isinstance(payload, dict):
                logger.warning("Skipping non-object payload on line %d in %s", idx, jsonl_path)
                continue

            rows.append(_normalize_episode(payload))

    df = pd.DataFrame(rows)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[REQUIRED_COLUMNS + [col for col in df.columns if col not in REQUIRED_COLUMNS]]


def _run_cli(args: List[str]) -> None:
    """Entry point for ``python -m analysis.load_dataset``."""

    if not args:
        print("Usage: python -m analysis.load_dataset <path-to-jsonl>")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    jsonl_path = args[0]
    df = load_episodes(jsonl_path)

    print(df.head())
    if "attacker_profile" in df.columns:
        print("\n[attacker_profile counts]")
        print(df["attacker_profile"].value_counts(dropna=False))


def main() -> None:
    _run_cli(sys.argv[1:])


if __name__ == "__main__":
    main()
