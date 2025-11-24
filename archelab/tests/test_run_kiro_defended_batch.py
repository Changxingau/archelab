import json

import pytest

pd = pytest.importorskip("pandas")

from archelab.defense import DefenseConfig
from scripts.run_kiro_defended_batch import generate_defended_episodes, main
from analysis.load_dataset import load_episodes


def test_generate_defended_episodes_basic_count():
    episodes = list(
        generate_defended_episodes(
            num_episodes=10, defense_config=DefenseConfig(profile_name="test_profile")
        )
    )

    assert len(episodes) == 10
    for episode in episodes:
        assert episode["topology"] == "defended"
        assert episode["defense_enabled"] is True
        assert episode["defense_profile"] == "test_profile"
        summary = episode.get("defense_summary") or {}
        assert {
            "redacted_leaks",
            "blocked_writes",
            "generic_refusals",
        } <= set(summary.keys())


def test_main_writes_jsonl(tmp_path):
    out = tmp_path / "defended.jsonl"
    exit_code = main(["-n", "3", "-o", str(out)])

    assert exit_code == 0
    assert out.is_file()

    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3

    for line in lines:
        obj = json.loads(line)
        assert obj["topology"] == "defended"
        assert obj["defense_enabled"] is True
        assert "trace" in obj


def test_load_dataset_on_defended_output(tmp_path):
    out = tmp_path / "defended.jsonl"

    exit_code = main(["-n", "2", "-o", str(out)])
    assert exit_code == 0

    df = load_episodes(str(out))

    assert len(df) == 2
    assert (df["topology"] == "defended").all()
    assert df["defense_enabled"].notna().all()
    assert df["attack_success"].notna().all()
