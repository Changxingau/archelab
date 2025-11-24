"""Lightweight wrappers for loading Archelab datasets via the packaged module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from analysis.load_dataset import load_episodes as _load_episodes


def load_episodes(jsonl_path: Path | str):
    """Load JSONL episodes into a pandas DataFrame.

    This mirrors :func:`analysis.load_dataset.load_episodes` but is re-exported
    under the packaged ``archelab.analysis`` namespace for convenience.
    """

    return _load_episodes(str(jsonl_path))


def load_dataset(jsonl_path: Path | str) -> List[Dict[str, Any]]:
    """Return dataset rows as dictionaries for convenience in tests and notebooks."""

    df = _load_episodes(str(jsonl_path))
    return df.to_dict("records")


__all__ = ["load_dataset", "load_episodes"]
