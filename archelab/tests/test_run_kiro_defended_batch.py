import json

from archelab.defense import DefenseConfig
from scripts.run_kiro_defended_batch import generate_defended_episodes, main


def test_generate_defended_episodes_basic_count():
    episodes = list(
        generate_defended_episodes(
            num_episodes=10, defense_config=DefenseConfig(profile_name="test_profile")
        )
    )

    assert len(episodes) == 10
    for episode in episodes:
        result = episode["result"]
        assert result["topology"] == "defended"
        assert result["defense_enabled"] is True
        assert result["defense_profile"] == "test_profile"
        summary = result.get("defense_summary") or {}
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
        assert obj["result"]["topology"] == "defended"
        assert obj["result"]["defense_enabled"] is True
