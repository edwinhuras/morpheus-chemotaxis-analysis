import json

with open('notebooks/01_bulk_collision_analysis.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 1. Config block
        if "SKIP_INITIAL_FRAMES = 15" in source:
            source = source.replace("# Number of initial frames to skip (cell settling period)", "# Number of initial MCS timesteps to skip (cell settling period)")
            source = source.replace("SKIP_INITIAL_FRAMES = 15", "SKIP_INITIAL_MCS = 150")
            source = source.replace("print(f\"Skip initial frames: {SKIP_INITIAL_FRAMES}\")", "print(f\"Skip initial MCS: {SKIP_INITIAL_MCS}\")")
            cell['source'] = [line + '\n' for line in source.split('\n')][:-1]

        # 2. Logic block
        if "frames_skipped = min(SKIP_INITIAL_FRAMES, total_frames)" in source:
            old_skipped = "    frames_skipped = min(SKIP_INITIAL_FRAMES, total_frames)"
            new_skipped = "    frames_skipped = sum(1 for t, fp in png_files if t < SKIP_INITIAL_MCS)"
            source = source.replace(old_skipped, new_skipped)
            
            old_if = "        if i >= SKIP_INITIAL_FRAMES:"
            new_if = "        if timestep >= SKIP_INITIAL_MCS:"
            source = source.replace(old_if, new_if)
            
            cell['source'] = [line + '\n' for line in source.split('\n')][:-1]

with open('notebooks/01_bulk_collision_analysis.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
