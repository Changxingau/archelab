from pathlib import Path

import pytest

from kiro_integrations.kiro_orchestrator import run_insecure_kiro_episode


SECRET = "SECRET_FOR_TESTING"


def test_direct_leak_profile_flags_secret(tmp_path: Path) -> None:
    dataset_path = tmp_path / "direct.jsonl"

    result = run_insecure_kiro_episode(
        repo_path=str(tmp_path),
        secret=SECRET,
        attacker_profile="direct_leak",
        dataset_path=dataset_path,
    )

    assert isinstance(result, dict)
    assert result["contains_secret_in_msg"] is True
    assert result["attack_success"] is True
    assert dataset_path.exists()


def test_backdoor_profile_flags_unauthorized_write(tmp_path: Path) -> None:
    dataset_path = tmp_path / "backdoor.jsonl"

    result = run_insecure_kiro_episode(
        repo_path=str(tmp_path),
        secret=SECRET,
        attacker_profile="backdoor_dropper",
        dataset_path=dataset_path,
    )

    assert result["unauthorized_write"] is True
    assert result["attack_success"] is True



def test_cautious_profile_blocks_attack(tmp_path: Path) -> None:
    dataset_path = tmp_path / "cautious.jsonl"

    result = run_insecure_kiro_episode(
        repo_path=str(tmp_path),
        secret=SECRET,
        attacker_profile="cautious",
        dataset_path=dataset_path,
    )

    assert result["attack_success"] is False
    assert result["contains_secret_in_msg"] is False
    assert result["unauthorized_write"] is False
    assert result["task_success"] is True



def test_unknown_profile_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_insecure_kiro_episode(
            repo_path=str(tmp_path),
            secret=SECRET,
            attacker_profile="unknown-profile",
            dataset_path=tmp_path / "unknown.jsonl",
        )
