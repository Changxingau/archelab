"""Utilities for exporting episode runs into dataset-friendly formats.

MAS engines such as Kiro should use these helpers after an episode completes
so downstream evaluation tooling can consume the results without custom
parsing. JSONL captures the full trace, while CSV provides quick statistics.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, Dict, Iterable, Union

from archelab.models.episode_result import EpisodeResult

PathLike = Union[str, Path]


EXTRA_DEFENSE_FIELDS = [
    "defense_redacted_leaks",
    "defense_blocked_writes",
    "defense_generic_refusals",
]


def episode_result_to_row(result: EpisodeResult) -> dict[str, Any]:
    """Convert an ``EpisodeResult`` into a flat row for CSV/analysis."""

    row = asdict(result)
    summary = row.get("defense_summary") or {}

    row["defense_enabled"] = bool(row.get("defense_enabled"))
    row["defense_profile"] = row.get("defense_profile") or "none"
    row["defense_redacted_leaks"] = int(summary.get("redacted_leaks", 0))
    row["defense_blocked_writes"] = int(summary.get("blocked_writes", 0))
    row["defense_generic_refusals"] = int(summary.get("generic_refusals", 0))

    return row


def append_episode_jsonl(path: PathLike, result: EpisodeResult, trace_json: Dict[str, Any]) -> None:
    """Append a single episode to a JSONL file.

    MAS engines should call this after computing the episode summary to persist
    the structured result alongside the full trace for later analysis.

    Each line in the file MUST be a valid JSON object containing:
    - all fields from ``EpisodeResult`` (flattened via ``dataclasses.asdict``)
    - a ``trace`` field containing the full episode trace as a nested JSON structure.

    If the file does not exist, create it. If it exists, append a new line. The
    function must NOT raise if the directory already exists.
    """

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(result)
    payload["trace"] = trace_json

    with target_path.open("a", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
        f.write("\n")


def write_episodes_csv(path: PathLike, results: Iterable[EpisodeResult]) -> None:
    """Write a collection of ``EpisodeResult`` objects to a CSV file.

    Designed for MAS engines to export lightweight summaries that can be sliced
    quickly with spreadsheet tools or basic scripts. Overwrites any existing
    file.

    - Overwrite the file if it already exists.
    - One row per episode.
    - Columns cover all public fields of the ``EpisodeResult`` dataclass.
    - Trace details are intentionally omitted; use JSONL for deep analysis.
    """

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    base_fields = [
        field.name for field in fields(EpisodeResult) if not field.name.startswith("_")
    ]
    field_names = base_fields + EXTRA_DEFENSE_FIELDS

    with target_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        for result in results:
            writer.writerow(episode_result_to_row(result))
