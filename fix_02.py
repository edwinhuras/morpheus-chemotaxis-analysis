import json

with open('notebooks/02_visualize_results.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Add the ignored simulation IDs
        if "IGNORE_SIM_IDS = []" in source:
            source = source.replace("IGNORE_SIM_IDS = []", "IGNORE_SIM_IDS = ['1205', '31', '1941']")
            cell['source'] = [line + '\n' for line in source.split('\n')][:-1]
            
        # Update overview plots to split by track type
        if "create_overview_plots(summary_df)" in source and "def create_overview_plots" in source:
            old_call = "create_overview_plots(summary_df)"
            new_call = """# Generate separate overview plots for each track type
for track_type in sorted(summary_df['track_type'].dropna().unique()):
    track_df = summary_df[summary_df['track_type'] == track_type]
    if len(track_df) > 0:
        create_overview_plots(track_df, title_suffix=f" — {track_type}")"""
            source = source.replace(old_call, new_call)
            cell['source'] = [line + '\n' for line in source.split('\n')][:-1]
            
        # Update filtered overview
        if "create_overview_plots(filtered, f' (>{MIN_PROGRESS}% Progress)')" in source:
            old_filtered = "create_overview_plots(filtered, f' (>{MIN_PROGRESS}% Progress)')"
            new_filtered = """for track_type in sorted(filtered['track_type'].dropna().unique()):
        track_df = filtered[filtered['track_type'] == track_type]
        if len(track_df) > 0:
            create_overview_plots(track_df, title_suffix=f" — {track_type} (>{MIN_PROGRESS}% Progress)")"""
            source = source.replace(old_filtered, new_filtered)
            cell['source'] = [line + '\n' for line in source.split('\n')][:-1]

with open('notebooks/02_visualize_results.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
