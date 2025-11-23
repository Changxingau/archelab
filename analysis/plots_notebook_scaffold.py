"""Scaffold script for future conversion into a Jupyter notebook.

This pseudo-notebook demonstrates how to generate ArcheRisk paper-ready
visualizations using the existing analysis and plotting utilities.
"""

# %% [markdown]
# # Archelab × Kiro – Phase 4.3 Visualization
# This scaffold will be converted to a Jupyter notebook.

# %%
from analysis.load_dataset import load_episodes
from analysis.compute_metrics import compute_metrics
from analysis.plot_scripts import (
    plot_attack_success_by_attacker_profile,
    plot_archetype_risk_profile,
)

JSONL_PATH = "data/kiro_insecure.jsonl"

# %% [markdown]
# ## Load the dataset
# Using `load_episodes` ensures we get a tidy DataFrame ready for metrics.

# %%
df = load_episodes(JSONL_PATH)
print("Loaded episodes DataFrame:")
print(df.head())

# %% [markdown]
# ## Compute aggregate metrics
# The default configuration computes core MAS security metrics.

# %%
metrics_default = compute_metrics(JSONL_PATH)
print("Default metrics head:")
print(metrics_default.head())

# %% [markdown]
# ## Plot 1: Attack success rate by attacker profile
# Saves the figure to `analysis/outputs/attack_success_by_attacker_profile.png`.

# %%
fig1 = plot_attack_success_by_attacker_profile(
    JSONL_PATH,
    "analysis/outputs/attack_success_by_attacker_profile.png",
)
print("Saved attack success plot:", fig1)

# %% [markdown]
# ## Plot 2: Behavior archetype risk profile
# Saves the figure to `analysis/outputs/behavior_archetype_risk_profile.png`.

# %%
fig2 = plot_archetype_risk_profile(
    JSONL_PATH,
    output_path="analysis/outputs/behavior_archetype_risk_profile.png",
)
print("Saved archetype risk profile plot:", fig2)

# %% [markdown]
# ## Next steps
# - Run this script locally or convert it to `.ipynb` with `jupytext`.
# - Adjust `JSONL_PATH` to point to your dataset.
# - Modify figure paths as needed for paper-ready exports.
