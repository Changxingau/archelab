"""Scaffold script to convert into a Jupyter notebook for ArcheRisk visuals.

This module demonstrates how to load episodes, compute metrics, and generate
paper-ready plots for the ArcheRisk manuscript. The script is structured like a
notebook so it can be converted to ``.ipynb`` (e.g., via jupytext) for
interactive exploration.
"""

# %% [markdown]
# # Archelab × Kiro – Phase 4.3 Visualization
# This scaffold will be converted to a Jupyter notebook.
# Use it to generate paper-ready ArcheRisk plots.

# %%
from archelab.analysis.load_dataset import load_episodes
from analysis.compute_metrics import compute_metrics
from analysis.plot_scripts import (
    plot_attack_success_by_attacker_profile,
    plot_archetype_risk_profile,
)

JSONL_PATH = "data/kiro_insecure.jsonl"

# %% [markdown]
# ## Load the dataset
# The helper below loads the JSONL episodes into a pandas DataFrame so we can
# inspect the columns that are available for analysis.

# %%
df = load_episodes(JSONL_PATH)
print(df.head())

# %% [markdown]
# ## Compute baseline metrics
# Use the default grouping options to calculate attack success and related
# metrics before any additional customization.

# %%
metrics_default = compute_metrics(JSONL_PATH)
print(metrics_default.head())

# %% [markdown]
# ## Plot attack success by attacker profile
# This plot shows how success rates differ across attacker profiles. The figure
# is saved to ``analysis/outputs/attack_success_by_attacker_profile.png``.

# %%
fig1 = plot_attack_success_by_attacker_profile(
    JSONL_PATH,
    "analysis/outputs/attack_success_by_attacker_profile.png",
)

# %% [markdown]
# ## Plot behavior archetype risk profile
# Compare attack success, secret leakage, and unauthorized writes across
# behavior archetypes (or other groupings if you provide ``groupby_levels``).
# The figure is saved to ``analysis/outputs/behavior_archetype_risk_profile.png``.

# %%
fig2 = plot_archetype_risk_profile(
    JSONL_PATH,
    output_path="analysis/outputs/behavior_archetype_risk_profile.png",
)
