import json

def update_ignore_ids(filename, variable_name):
    with open(filename, 'r') as f:
        nb = json.load(f)

    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if f"{variable_name} = []" in source:
                source = source.replace(f"{variable_name} = []", f"{variable_name} = ['1205', '31', '1941']")
                cell['source'] = [line + '\n' for line in source.split('\n')][:-1]
                print(f"Updated {filename}")

    with open(filename, 'w') as f:
        json.dump(nb, f, indent=1)

update_ignore_ids('notebooks/01_bulk_collision_analysis.ipynb', 'EXCLUDE_SIMULATION_IDS')
update_ignore_ids('notebooks/03_cell_shape_visuals.ipynb', 'IGNORE_SIM_IDS')
