import pandas as pd
import glob
import os

path = '/Users/edwinhuras/Desktop/USRA_2025/Code/Utilities/morpheus-chemotaxis-analysis/data/processed_full'

replacements = {
    'GapsSlalom': 'TrackA',
    'SlalomMedium': 'TrackB',
    'SlalomMed': 'TrackB',
    'WPIPIP3': 'WPI-PIP3',
    'WPPIP3': 'WPI-PIP3',
    '2xWPFix': 'Rac-Rho',
    '2xWPTension': 'Rac-Rho-T'
}

def apply_replacements(val):
    if not isinstance(val, str):
        return val
    for k, v in replacements.items():
        val = val.replace(k, v)
    return val

for file in glob.glob(os.path.join(path, '*')):
    if file.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.endswith('.pkl'):
        df = pd.read_pickle(file)
    else:
        continue
    
    # Determine track from filename for building folder_name
    track = 'TrackA' if 'TRACKA' in os.path.basename(file) else 'TrackB'

    # Apply replacements to string columns
    for col in df.columns:
        if df[col].dtype.name in ['object', 'string', 'str']:
            df[col] = df[col].map(lambda x: apply_replacements(x) if isinstance(x, str) else x)
        elif df[col].dtype.name == 'category':
            df[col] = df[col].astype(str).map(lambda x: apply_replacements(x) if isinstance(x, str) else x).astype('category')

    # Reconstruct folder_name and folder_path if columns exist
    if all(c in df.columns for c in ['model_type', 'simulation_id']):
        if 'folder_name' in df.columns:
            df['folder_name'] = df['model_type'] + '_Collision_' + track + '_' + df['simulation_id'].astype(str)
            
        if 'folder_path' in df.columns:
            df['folder_path'] = 'data/' + df['model_type'] + '_Collision_' + track + '_' + df['simulation_id'].astype(str)

    # Save
    if file.endswith('.csv'):
        df.to_csv(file, index=False)
    elif file.endswith('.pkl'):
        df.to_pickle(file)
        
    print(f"Processed {os.path.basename(file)}")
    
print("Renaming completed successfully.")
