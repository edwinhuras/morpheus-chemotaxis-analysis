import json

with open('notebooks/01_bulk_collision_analysis.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "    return summary, detailed_rows" not in source and "def process_simulation_folder" in source:
            # We need to append the return statement
            cell['source'].append("    return summary, detailed_rows\n")
            print("Appended return statement")

with open('notebooks/01_bulk_collision_analysis.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
