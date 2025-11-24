from archelab.defense import DefenseConfig
from kiro_integrations.kiro_defended_orchestrator import run_single_defended_episode


def test_defended_episode_populates_result_fields():
    result_dict, trace_dict = run_single_defended_episode(
        task_id="test_task",
        task_description="Verify defended episode completeness",
        repo_path="./repo",
        secret="SECRET_TOKEN_123",
        attacker_profile="direct_leak",
        defense_config=DefenseConfig(profile_name="minimal_v1"),
    )

    result = result_dict

    assert result["task_success"] is not None
    assert result["attack_success"] is not None
    assert result["topology"] == "defended"
    assert result["attacker_profile"] == "direct_leak"

    assert result["defense_enabled"] is True
    assert result["defense_profile"] == "minimal_v1"

    summary = result["defense_summary"]
    assert isinstance(summary, dict)
    assert {"redacted_leaks", "blocked_writes", "generic_refusals"} <= set(summary.keys())
    assert all(isinstance(value, int) and value >= 0 for value in summary.values())
