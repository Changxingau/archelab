import json
import subprocess
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

from analysis.load_dataset import load_episodes


def test_insecure_batch_writes_flat_jsonl(tmp_path: Path) -> None:
    output_path = tmp_path / "insecure.jsonl"

    subprocess.check_call(
        [
            "python",
            "-m",
            "scripts.run_kiro_insecure_batch",
            "-n",
            "2",
            "-o",
            str(output_path),
        ]
    )

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    entry = json.loads(lines[0])

    assert "task_success" in entry
    assert "attack_success" in entry
    assert "leakage" in entry
    assert "unauthorized_write" in entry
    assert entry.get("topology") == "insecure"
    assert "attacker_profile" in entry

    assert "trace" in entry
    assert isinstance(entry["trace"], dict)


def test_load_dataset_reads_insecure_jsonl(tmp_path: Path) -> None:
    output_path = tmp_path / "insecure.jsonl"

    subprocess.check_call(
        [
            "python",
            "-m",
            "scripts.run_kiro_insecure_batch",
            "-n",
            "3",
            "-o",
            str(output_path),
        ]
    )

    df = load_episodes(str(output_path))

    assert len(df) == 3
    for column in ["task_success", "attack_success", "leakage", "unauthorized_write"]:
        assert pd.notna(df[column]).all()
