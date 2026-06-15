import os
import shutil
from pathlib import Path

# Source: Old Track A WPIPIP3 run
src_dir = Path("/Users/edwinhuras/Desktop/USRA_2025/Code/Utilities/CollisionDetection_GapsSlalom/GapsSlalom/Figure6_WPIPIP3_Maze_Collision_1159")

# Destination: New sample folder
dest_dir = Path("/Users/edwinhuras/Desktop/USRA_2025/Code/Utilities/morpheus-chemotaxis-analysis/data/sample_simulations/WPIPIP3_Track_Collision_TrackA_1159")

# Create dest if it doesn't exist
dest_dir.mkdir(parents=True, exist_ok=True)

# Copy celltracks.xml
if (src_dir / "celltracks.xml").exists():
    shutil.copy2(src_dir / "celltracks.xml", dest_dir / "celltracks.xml")

# Copy domain file and rename to standard
src_domain = src_dir / "GapsSlalom_300x450.tiff"
if src_domain.exists():
    shutil.copy2(src_domain, dest_dir / "TrackA_300x450.tiff")

# Copy every 100th PNG plot frame (up to 1500)
for t in range(0, 1600, 100):
    src_png = src_dir / f"plot_{t:05d}.png"
    if src_png.exists():
        dest_png = dest_dir / f"plot_{t:05d}.png"
        shutil.copy2(src_png, dest_png)

print(f"Packaged new sample: {dest_dir}")
