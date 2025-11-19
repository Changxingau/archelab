"""Utilities for exporting episode data for downstream benchmarks.

These helpers are intentionally framework-agnostic so any MAS engine (e.g. Kiro)
can persist finished episodes in standardized formats. Engines should call these
functions after an episode is finalized to export summary data alongside the
recorded trace.
"""

from dataclasses import asdict
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Union

from archelab.models.episode_result import EpisodeResult

PathLike = Union[str, Path]


def append_episode_jsonl(path: PathLike, result: EpisodeResult, trace_json: Dict[str, Any]) -> None:
    """Append a single episode to a JSONL file.

    Each line in the file contains all fields from ``EpisodeResult`` (flattened
    via ``dataclasses.asdict``) plus a ``trace`` key holding the serialized trace
    emitted by the episode recorder. This is intended for deep analysis and can
    be used by Kiro or other MAS engines after ``finalize_episode`` completes.

    If the file does not exist it will be created. Parent directories are
    created if necessary. Appending to an existing file will add a single JSON
    object per line encoded as UTF-8. This function does not raise if the parent
    directory already exists.
    """

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    payload: Dict[str, Any] = {**asdict(result), "trace": trace_json}

    with file_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False))
        f.write("\n")


def write_episodes_csv(path: PathLike, results: Iterable[EpisodeResult]) -> None:
    """Write a collection of ``EpisodeResult`` objects to a CSV file.

    Use this for quick statistics where the full trace is not required. The CSV
    will be overwritten if it already exists. Columns are derived from the keys
    of the first ``EpisodeResult`` encountered; each subsequent episode is
    written with the same ordering. If no results are provided an empty file is
    created and no header is written.
    """

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    iterator = iter(results)
    try:
        first_result = next(iterator)
    except StopIteration:
        # Create an empty file and exit early when no data is provided.
        file_path.touch()
        return

    first_row = asdict(first_result)
    fieldnames = list(first_row.keys())

    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(first_row)
        for result in iterator:
            writer.writerow(asdict(result))
