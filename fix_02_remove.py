import json

with open('notebooks/02_visualize_results.ipynb', 'r') as f:
    nb = json.load(f)

# Keep all cells except the markdown cell containing "Per-Simulation Collision Timeseries"
# and the code cell containing "plot_simulation_timeseries(sim_id)"
new_cells = []
for cell in nb['cells']:
    source = "".join(cell.get('source', []))
    if "Per-Simulation Collision Timeseries" in source:
        continue
    if "def plot_simulation_timeseries" in source:
        continue
    new_cells.append(cell)

nb['cells'] = new_cells

with open('notebooks/02_visualize_results.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
