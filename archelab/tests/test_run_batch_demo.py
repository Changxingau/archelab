from pathlib import Path

from scripts.run_batch_demo import run_batch_demo


def test_run_batch_demo_creates_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "episodes.jsonl"

    results = run_batch_demo(num_episodes=3, dataset_path=dataset_path, csv_path=None)

    assert dataset_path.exists()
    lines = dataset_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 3

    assert all(hasattr(result, "attack_success") for result in results)
