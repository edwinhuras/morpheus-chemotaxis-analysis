import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Repository root for path resolution
REPO_ROOT = Path(os.getcwd()).parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

print("Imports successful.")

# ============================================================================
# USER CONFIGURATION
# ============================================================================

# Path to processed data (output from 01_bulk_collision_analysis)
DATA_DIR = REPO_ROOT / "output"

# --- Font sizes for consistent, publication-quality plots ---
TITLE_FONTSIZE = 22
SUBTITLE_FONTSIZE = 18
AXIS_LABEL_FONTSIZE = 16
TICK_LABEL_FONTSIZE = 14

# --- Model type renaming for cleaner labels ---
# Maps internal model names to display names used in the paper
MODEL_NAME_MAP = {
    'RacRho': 'RacRho',
    'RacRho_T': 'RacRho_T',
}

# --- Model types to EXCLUDE from visualization ---
# These were experimental models not included in the final paper
IGNORE_MODEL_TYPES = [
    '2xWP', 'RacProtrusion', 'RacProtrusionNoise',
    'RacProtrusionRhoContraction', 'RacProtrusionRhoContractionNoise',
    'RacProtrusionNoiseFix', 'RacProtrusionRhoContractionNoiseFix',
    'RacProtrusionRhoContractionTension',
]

# --- Simulation IDs to exclude ---
IGNORE_SIM_IDS = []

# --- Consistent color scheme for each model type ---
MODEL_COLOR_MAP = {
    'WP':        '#1f77b4',  # Blue
    'WPI':       '#ff7f0e',  # Orange
    'WPIPIP3':   '#2ca02c',  # Green
    'RacRho':    '#d62728',  # Red
    'RacRho_T':  '#9467bd',  # Purple
}

# --- X-position analysis bounds (domain coordinates) ---
X_AXIS_MIN = 0
X_AXIS_MAX = 300

# --- Centroid Y thresholds for filtering active migration ---
MIN_CENTROID_Y = 50
MAX_CENTROID_Y = 400

print("Configuration loaded.")

def get_model_color(model_type, fallback_index=0):
    """Get the consistent color for a model type."""
    if model_type in MODEL_COLOR_MAP:
        return MODEL_COLOR_MAP[model_type]
    fallback = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    return fallback[fallback_index % len(fallback)]


def get_model_colors(model_list):
    """Get colors for a list of models."""
    return [get_model_color(m, i) for i, m in enumerate(model_list)]

# Load processed data (prefer pickle for speed, fall back to CSV)
summary_pkl = DATA_DIR / 'collision_analysis_summary.pkl'
detailed_pkl = DATA_DIR / 'collision_analysis_detailed.pkl'

if summary_pkl.exists():
    summary_df = pd.read_pickle(summary_pkl)
else:
    summary_df = pd.read_csv(DATA_DIR / 'collision_analysis_summary.csv')

if detailed_pkl.exists():
    detailed_df = pd.read_pickle(detailed_pkl)
else:
    detailed_df = pd.read_csv(DATA_DIR / 'collision_analysis_detailed.csv')

print(f"Loaded: {len(summary_df)} simulations, {len(detailed_df)} frames")
print(f"Model types (raw): {summary_df['model_type'].unique()}")

# Apply filters
if IGNORE_SIM_IDS:
    summary_df = summary_df[
        ~summary_df['simulation_id'].astype(str).isin(IGNORE_SIM_IDS)
    ].copy()
    detailed_df = detailed_df[
        ~detailed_df['simulation_id'].astype(str).isin(IGNORE_SIM_IDS)
    ].copy()

if IGNORE_MODEL_TYPES:
    summary_df = summary_df[
        ~summary_df['model_type'].isin(IGNORE_MODEL_TYPES)
    ].copy()

# Remove rows with missing model type
summary_df = summary_df.dropna(subset=['model_type'])

# Rename model types for display
summary_df['model_type'] = summary_df['model_type'].replace(MODEL_NAME_MAP)
if 'model_type' in detailed_df.columns:
    detailed_df['model_type'] = detailed_df['model_type'].replace(MODEL_NAME_MAP)

# Filter detailed_df to only include simulations present in summary
valid_ids = set(summary_df['simulation_id'].astype(str).unique())
detailed_df = detailed_df[
    detailed_df['simulation_id'].astype(str).isin(valid_ids)
].copy()

print(f"After filtering: {len(summary_df)} simulations, {len(detailed_df)} frames")
print(f"Model types: {sorted(summary_df['model_type'].unique())}")
print(f"Track types: {summary_df['track_type'].dropna().unique()}")

def create_overview_plots(df, title_suffix=""):
    """Create overview collision statistics."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"Collision Analysis Overview{title_suffix}",
                 fontsize=TITLE_FONTSIZE, y=1.05)

    model_types = sorted(df["model_type"].unique())
    colors = get_model_colors(model_types)

    # --- Col 1: Mean Collision Intensity Bar Chart ---
    ax = axes[0]
    stats_agg = df.groupby("model_type")["mean_collision_intensity"].agg(["mean", "std"])
    stats_agg = stats_agg.reindex(model_types)
    bar_colors = get_model_colors(stats_agg.index.tolist())

    stats_agg["mean"].plot(kind="bar", ax=ax, color=bar_colors, alpha=0.8)
    
    # Fix error bars so they do not go below 0
    lower_error = np.minimum(stats_agg["mean"], stats_agg["std"])
    upper_error = stats_agg["std"]
    yerr = np.array([lower_error, upper_error])
    
    ax.errorbar(range(len(stats_agg)), stats_agg["mean"],
                yerr=yerr, fmt="none", color="black",
                capsize=5, linewidth=1.5)
                
    ax.set_title("Mean Collision Intensity", fontsize=SUBTITLE_FONTSIZE)
    ax.set_ylabel("Mean Intensity", fontsize=AXIS_LABEL_FONTSIZE)
    ax.tick_params(axis="x", rotation=45, labelsize=TICK_LABEL_FONTSIZE)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONTSIZE)
    ax.grid(True, alpha=0.3)

    # --- Col 2: Track Progress vs Mean Collision Intensity ---
    from matplotlib.colors import ListedColormap
    n_models = len(model_types)
    model_to_code = {m: i for i, m in enumerate(model_types)}
    color_codes = df["model_type"].map(model_to_code)
    custom_cmap = ListedColormap(colors)

    scatter = axes[1].scatter(
        df["track_progress_percentage"], df["mean_collision_intensity"],
        c=color_codes, cmap=custom_cmap, alpha=0.6, s=50,
        vmin=0, vmax=max(n_models - 1, 1),
    )
    axes[1].set_xlabel("Track Progress %", fontsize=AXIS_LABEL_FONTSIZE)
    axes[1].set_ylabel("Mean Collision Intensity", fontsize=AXIS_LABEL_FONTSIZE)
    axes[1].set_title("Progress vs Mean Collision Intensity", fontsize=SUBTITLE_FONTSIZE)
    axes[1].tick_params(labelsize=TICK_LABEL_FONTSIZE)
    axes[1].grid(True, alpha=0.3)

    if n_models > 1:
        cbar = plt.colorbar(scatter, ax=axes[1], ticks=range(n_models))
        cbar.set_label("Model Type", fontsize=AXIS_LABEL_FONTSIZE)
        cbar.set_ticklabels(model_types)

    plt.tight_layout()
    plt.show()

create_overview_plots(summary_df)

MIN_PROGRESS = 10  # Minimum track progress % to include

filtered = summary_df[summary_df['track_progress_percentage'] > MIN_PROGRESS].copy()
print(f"Filtered to {len(filtered)} simulations with >{MIN_PROGRESS}% progress")
print(f"(Excluded {len(summary_df) - len(filtered)} low-progress simulations)")

if len(filtered) > 0:
    create_overview_plots(filtered, f' (>{MIN_PROGRESS}% Progress)')
else:
    print("No simulations meet the progress threshold.")

def plot_simulation_timeseries(sim_id):
    """Plot collision intensity over time for a single simulation."""
    sim_data = detailed_df[
        detailed_df["simulation_id"].astype(str) == str(sim_id)
    ].sort_values("timestep")

    if sim_data.empty:
        print(f"No data for simulation {sim_id}")
        return

    model_type = sim_data["model_type"].iloc[0] if "model_type" in sim_data.columns else "Unknown"
    color = get_model_color(model_type)

    fig, ax1 = plt.subplots(figsize=(14, 4))

    # Collision intensity timeline
    ax1.fill_between(sim_data["timestep"], sim_data["collision_intensity"],
                     alpha=0.3, color=color)
    ax1.plot(sim_data["timestep"], sim_data["collision_intensity"],
             color=color, linewidth=0.8)
    ax1.set_ylabel("Collision Intensity", fontsize=AXIS_LABEL_FONTSIZE)
    ax1.set_xlabel("Timestep", fontsize=AXIS_LABEL_FONTSIZE)
    ax1.set_title(f"Simulation {sim_id} ({model_type}) — Collision Timeline",
                  fontsize=TITLE_FONTSIZE)
    ax1.tick_params(labelsize=TICK_LABEL_FONTSIZE)
    ax1.grid(True, alpha=0.3)

    # Summary stats
    total = len(sim_data)
    colliding = sim_data["collision"].sum()
    ax1.text(0.02, 0.95,
             f"Collision: {colliding}/{total} frames ({colliding/total*100:.1f}%)",
             transform=ax1.transAxes, fontsize=TICK_LABEL_FONTSIZE,
             verticalalignment="top",
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    plt.tight_layout()
    plt.show()

# Plot the first 3 simulations as examples
for sim_id in summary_df["simulation_id"].unique()[:3]:
    plot_simulation_timeseries(sim_id)

def run_statistical_comparisons(df, metric='collision_percentage'):
    """Run pairwise independent t-tests between model types."""
    model_types = sorted(df['model_type'].dropna().unique())
    n = len(model_types)

    if n < 2:
        print("Need at least 2 model types for comparison.")
        return

    results = []
    for i in range(n):
        for j in range(i + 1, n):
            m1, m2 = model_types[i], model_types[j]
            d1 = df[df['model_type'] == m1][metric].dropna()
            d2 = df[df['model_type'] == m2][metric].dropna()

            if len(d1) > 1 and len(d2) > 1:
                t_stat, p_val = stats.ttest_ind(d1, d2)
                sig = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
                results.append({
                    'Model 1': m1,
                    'Model 2': m2,
                    'Mean 1': f'{d1.mean():.2f}',
                    'Mean 2': f'{d2.mean():.2f}',
                    'n1': len(d1),
                    'n2': len(d2),
                    't-statistic': f'{t_stat:.3f}',
                    'p-value': f'{p_val:.4f}',
                    'Significance': sig,
                })

    if results:
        results_df = pd.DataFrame(results)
        print(f"\nPairwise t-tests for '{metric}':")
        print(results_df.to_string(index=False))
    else:
        print("Not enough data for pairwise comparisons.")


for metric in ['collision_percentage', 'mean_collision_intensity',
               'max_collision_intensity']:
    run_statistical_comparisons(summary_df, metric)
    print()

print("=" * 60)
print("COLLISION DETECTION ANALYSIS REPORT")
print("=" * 60)
print(f"\nDataset: {len(summary_df)} simulations, {len(detailed_df)} frames")
print(f"Model types: {', '.join(sorted(summary_df['model_type'].unique()))}")
print(f"Track types: {', '.join(summary_df['track_type'].dropna().unique())}")
print()

# Overall collision rates
with_collision = (summary_df['collision_frames'] > 0).sum()
print(f"Simulations with collisions: {with_collision}/{len(summary_df)}")
print(f"  ({with_collision/len(summary_df)*100:.1f}%)")

print("\nCollision % by model type:")
print(summary_df.groupby('model_type').agg({
    'collision_percentage': ['mean', 'std', 'count'],
    'track_progress_percentage': ['mean', 'std'],
}).round(2))
