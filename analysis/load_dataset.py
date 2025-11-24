"""Development-time shim module.

Canonical implementation now lives in `archelab.analysis.load_dataset`.
This file exists only for backward compatibility for local notebooks/scripts
that import `analysis.load_dataset` directly.
"""

from archelab.analysis.load_dataset import load_dataset, load_episodes, REQUIRED_COLUMNS

__all__ = ["load_dataset", "load_episodes", "REQUIRED_COLUMNS"]
