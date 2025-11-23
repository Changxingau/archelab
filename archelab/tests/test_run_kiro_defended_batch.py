import json
from pathlib import Path

from archelab.defense import DefenseConfig
from scripts.run_kiro_defended_batch import generate_defended_episodes, main


def test_generate_defended_episodes_basic_count(tmp_path: Path) -> None:
    num = 10
    episodes = list(
        generate_defended_episodes(
            num_episodes=num,
            defense_config=DefenseConfig(profile_name="test_profile"),
            repo_path=str(tmp_path),
            secret="SECRET_TOKEN_ABC",
            seed=42,
        )
    )

    assert len(episodes) == num
    for episode in episodes:
        assert episode["topology"] == "defended"
        assert episode["defense_enabled"] is True
        assert episode["defense_profile"] == "test_profile"
        summary = episode.get("defense_summary") or {}
        assert {"redacted_leaks", "blocked_writes", "generic_refusals"} <= set(
            summary.keys()
        )


def test_main_writes_jsonl(tmp_path: Path) -> None:
    output = tmp_path / "defended.jsonl"
    exit_code = main(["-n", "3", "-o", str(output)])

    assert exit_code == 0
    assert output.is_file()

    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3

    for line in lines:
        obj = json.loads(line)
        assert obj["topology"] == "defended"
        assert obj["defense_enabled"] is True
