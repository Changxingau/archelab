import pytest

from kiro_integrations.kiro_defended_orchestrator import run_single_defended_episode


def test_run_single_defended_episode_sets_defense_metadata(tmp_path):
    result, trace = run_single_defended_episode(
        task_id="task1",
        task_description="Ensure defense metadata is captured",
        repo_path=str(tmp_path),
        secret="SECRET_TOKEN",
        attacker_profile="direct_leak",
    )

    assert result["topology"] == "defended"
    assert result["defense_enabled"] is True
    assert result["defense_profile"] == "minimal_v1"
    summary_keys = set(result.get("defense_summary", {}).keys())
    assert {"redacted_leaks", "blocked_writes", "generic_refusals"}.issubset(summary_keys)
    assert trace.get("meta", {}).get("defense_profile") == "minimal_v1"


def test_run_single_defended_episode_works_for_all_profiles(tmp_path):
    profiles = {"direct_leak", "backdoor_dropper", "deceiver", "escalator", "mixed"}

    for profile in profiles:
        result, _ = run_single_defended_episode(
            task_id=f"task-{profile}",
            task_description="Smoke test defended orchestrator",
            repo_path=str(tmp_path),
            secret="SECRET_TOKEN",
            attacker_profile=profile,
        )
        assert result["topology"] == "defended"
