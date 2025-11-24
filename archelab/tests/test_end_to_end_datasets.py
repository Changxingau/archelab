import json
import subprocess
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

from archelab.analysis.load_dataset import load_dataset


def test_batch_scripts_emit_flat_jsonl_for_insecure_and_defended(tmp_path: Path) -> None:
    insecure_path = tmp_path / "kiro_insecure_test.jsonl"
    defended_path = tmp_path / "kiro_defended_test.jsonl"

    subprocess.check_call(
        [
            "python",
            "-m",
            "scripts.run_kiro_insecure_batch",
            "-n",
            "5",
            "-o",
            str(insecure_path),
        ]
    )
    subprocess.check_call(
        [
            "python",
            "-m",
            "scripts.run_kiro_defended_batch",
            "-n",
            "5",
            "-o",
            str(defended_path),
        ]
    )

    insecure_lines = [
        line
        for line in insecure_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    defended_lines = [
        line
        for line in defended_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(insecure_lines) == 5
    assert len(defended_lines) == 5

    insecure_entry = json.loads(insecure_lines[0])
    defended_entry = json.loads(defended_lines[0])

    assert insecure_entry["topology"] == "insecure"
    assert isinstance(insecure_entry["task_success"], bool)
    assert isinstance(insecure_entry["attack_success"], bool)
    assert isinstance(insecure_entry["attacker_profile"], str)
    assert insecure_entry["defense_enabled"] is False
    assert "defense_summary" in insecure_entry and isinstance(
        insecure_entry["defense_summary"], dict
    )
    assert set(insecure_entry["defense_summary"].keys()) == {
        "redacted_leaks",
        "blocked_writes",
        "generic_refusals",
    }
    assert "trace" in insecure_entry and isinstance(insecure_entry["trace"], dict)

    assert defended_entry["topology"] == "defended"
    assert isinstance(defended_entry["task_success"], bool)
    assert isinstance(defended_entry["attack_success"], bool)
    assert isinstance(defended_entry["attacker_profile"], str)
    assert defended_entry["defense_enabled"] is True
    assert "defense_summary" in defended_entry and isinstance(
        defended_entry["defense_summary"], dict
    )
    assert set(defended_entry["defense_summary"].keys()) == {
        "redacted_leaks",
        "blocked_writes",
        "generic_refusals",
    }
    assert "trace" in defended_entry and isinstance(defended_entry["trace"], dict)


def test_load_dataset_reads_metrics_for_insecure_and_defended(tmp_path: Path) -> None:
    insecure_path = tmp_path / "kiro_insecure_test.jsonl"
    defended_path = tmp_path / "kiro_defended_test.jsonl"

    subprocess.check_call(
        [
            "python",
            "-m",
            "scripts.run_kiro_insecure_batch",
            "-n",
            "5",
            "-o",
            str(insecure_path),
        ]
    )
    subprocess.check_call(
        [
            "python",
            "-m",
            "scripts.run_kiro_defended_batch",
            "-n",
            "5",
            "-o",
            str(defended_path),
        ]
    )

    insecure_rows = load_dataset(Path(insecure_path))
    defended_rows = load_dataset(Path(defended_path))

    assert len(insecure_rows) == 5
    assert len(defended_rows) == 5

    for row in insecure_rows:
        assert row["topology"] == "insecure"
        assert isinstance(row["attacker_profile"], str)
        assert row["task_success"] is not None
        assert row["attack_success"] is not None

    for row in defended_rows:
        assert row["topology"] == "defended"
        assert isinstance(row["attacker_profile"], str)
        assert row["task_success"] is not None
        assert row["attack_success"] is not None
        assert "defense_summary" in row
        assert isinstance(row["defense_summary"], dict)
