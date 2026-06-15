import json

with open('notebooks/02_visualize_results.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        if "    if len(track_df) > 0:\n" in source and "create_overview_plots(track_df" not in source:
            if "track_df = summary_df[summary_df['track_type'] == track_type]" in source:
                cell['source'].append('        create_overview_plots(track_df, title_suffix=f" — {track_type}")\n')
            
        if "        if len(track_df) > 0:\n" in source and "create_overview_plots(track_df" not in source:
            if "track_df = filtered[filtered['track_type'] == track_type]" in source:
                cell['source'].append('            create_overview_plots(track_df, title_suffix=f" — {track_type} (>{MIN_PROGRESS}% Progress)")\n')
            
        # Fix missing print config load
        if "MIN_CENTROID_Y = 50\n" in source and "MAX_CENTROID_Y = 400\n" in source and "print(\"Configuration loaded.\")" not in source:
            cell['source'].append('print("Configuration loaded.")\n')
            
        # Fix missing print no simulations meet the progress threshold
        if "else:\n" in source and "print(\"No simulations meet the progress threshold.\")" not in source:
            cell['source'].append('    print("No simulations meet the progress threshold.")\n')

with open('notebooks/02_visualize_results.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
