"""Utilities for persisting episode outcomes to datasets.

MAS engines such as Kiro should call these helpers after finalizing an episode
so that experiment outputs are consistently appended to disk. JSONL keeps the
full trace for deep analysis, while CSV offers a lightweight summary for quick
statistics.
"""

import csv
import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, Dict, Iterable, Union

from archelab.models.episode_result import EpisodeResult

PathLike = Union[str, Path]


def append_episode_jsonl(path: PathLike, result: EpisodeResult, trace_json: Dict[str, Any]) -> None:
    """Append a single episode result and its trace to a JSONL file.

    MAS engines should invoke this after an episode is finalized to persist the
    structured outcome alongside the full execution trace. Each line in the
    target file is a standalone JSON object combining the flattened
    ``EpisodeResult`` payload with a nested ``trace`` entry.
    """

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    episode_dict = asdict(result)
    episode_dict["trace"] = trace_json

    with file_path.open("a", encoding="utf-8") as file:
        json.dump(episode_dict, file)
        file.write("\n")


def write_episodes_csv(path: PathLike, results: Iterable[EpisodeResult]) -> None:
    """Write a collection of episode results to a CSV file.

    Use this when an experiment batch is complete and you want quick,
    spreadsheet-friendly metrics. The output omits the full trace and captures
    only the public fields of ``EpisodeResult``.
    """

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    episode_fieldnames = [field.name for field in fields(EpisodeResult) if not field.name.startswith("_")]

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=episode_fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(asdict(result))
