# ArcheLab Minimal Orchestrator

This package contains a minimal experiment harness for MAS security experiments.
It is intentionally small and framework-agnostic so that you can plug in
different MAS engines (Kiro, AutoGen, ChatDev, MetaGPT, A2A, MCP, etc.) later.

## Structure

- `env_core/environment.py`  
  Minimal `Environment` abstraction for file operations, test execution, and
  secret checking. Currently uses stubbed I/O and can be extended to real
  repositories and test runners.

- `logging_utils/episode_recorder.py`  
  `EpisodeRecorder` collects meta information, agent messages, and
  environment/tool events and exposes a JSON-compatible trace.

- `models/episode_result.py`  
  `EpisodeResult` dataclass defines the unified schema for a single episode,
  including task success and attack success flags.

- `episodes/runner_minimal.py`  
  Minimal orchestrator with two agents (`worker` and `attacker`) sharing
  a common `Environment`. The LLM backend is still a stub (`call_llm`) and
  should be replaced with a real model call.

## Next Steps

- Plug in a real LLM backend in `call_llm`.
- Add parsing of explicit tool commands in `worker_reply` to invoke
  `Environment.read_file`, `Environment.write_file`, and `Environment.run_tests`.
- Implement CSV / JSON writers that consume `EpisodeResult` and episode traces.
- Add adapters for MAS frameworks such as AutoGen or ChatDev, while reusing
  the same `Environment`, `EpisodeRecorder`, and `EpisodeResult` schema.

## Phase 4 – Analysis & Plots

After installing the project in editable mode:

```
pip install -e .
```

You can generate basic MAS security plots from a JSONL dataset using:

```
python -m analysis.compute_metrics data/kiro_insecure.jsonl
python -m analysis.plot_scripts data/kiro_insecure.jsonl \
  --attack-success-path analysis/outputs/attack_success_by_attacker_profile.png \
  --archetype-risk-path analysis/outputs/behavior_archetype_risk_profile.png
```

The plots use the metrics computed in Phase 4 and are intended for inclusion
in ArcheRisk analyses such as the ArcheRisk paper.
