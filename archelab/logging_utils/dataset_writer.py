"""Utilities for exporting MAS experiment episodes for benchmarking.

This module provides lightweight, framework-agnostic helpers to persist
episode outcomes. MAS engines such as Kiro can call these functions after
an episode completes to record results for later analysis.
"""

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Union

from archelab.models.episode_result import EpisodeResult

PathLike = Union[str, Path]


def append_episode_jsonl(path: PathLike, result: EpisodeResult, trace_json: Dict[str, Any]) -> None:
    """Append a single episode record to a JSONL file.

    MAS engines should call this after finalizing an episode to store both the
    structured summary (`EpisodeResult`) and the full trace for deep analysis.

    Each line is a JSON object containing all fields from ``EpisodeResult`` plus
    a ``trace`` field with the provided trace data. The parent directory is
    created if necessary. If the file already exists, the new record is
    appended.
    """

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    record = asdict(result)
    record["trace"] = trace_json

    with output_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record))
        fp.write("\n")


def write_episodes_csv(path: PathLike, results: Iterable[EpisodeResult]) -> None:
    """Write a collection of episode summaries to a CSV file.

    Intended for quick statistics across many runs. Engines should call this
    when exporting batches of completed episodes. Only the public fields from
    ``EpisodeResult`` are included; full traces are intentionally omitted.

    If ``results`` is empty, an empty file is created. Existing files are
    overwritten.
    """

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results_list = list(results)
    with output_path.open("w", encoding="utf-8", newline="") as fp:
        if not results_list:
            return

        first_record = asdict(results_list[0])
        writer = csv.DictWriter(fp, fieldnames=list(first_record.keys()))
        writer.writeheader()
        writer.writerow(first_record)

        for result in results_list[1:]:
            writer.writerow(asdict(result))
