import json

with open('notebooks/01_bulk_collision_analysis.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "max_y_position, track_progress = get_progress_from_centroids(" in source:
            old_code = """    # --- Track progress ---
    max_y_position, track_progress = get_progress_from_centroids(
        centroids, height_for_progress
    )"""
            new_code = """    # --- Track progress ---
    # Filter centroids to only include up to the max timestep available in PNGs
    if png_files:
        max_png_timestep = max(t for t, fp in png_files)
        centroids = [c for c in centroids if c[0] <= max_png_timestep]
        
    max_y_position, track_progress = get_progress_from_centroids(
        centroids, height_for_progress
    )"""
            if old_code in source:
                new_source = source.replace(old_code, new_code)
                cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]
                print("Replaced code successfully")

with open('notebooks/01_bulk_collision_analysis.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
