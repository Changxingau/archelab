from pathlib import Path

from scripts.run_batch_demo import run_batch_demo


def test_run_batch_demo_writes_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "episodes.jsonl"

    results = run_batch_demo(
        num_episodes=3,
        dataset_path=dataset_path,
        csv_path=None,
        topology="test-topology",
        defense_profile="none",
        verbose_episodes=False,
    )

    assert dataset_path.exists()

    lines = dataset_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3

    assert len(results) == 3
    assert all(hasattr(result, "attack_success") for result in results)
