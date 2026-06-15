with open("README.md", "r") as f:
    text = f.read()

old_section = """### Step 2: Visualization & Statistics

The visualization notebook (`02_visualize_results.ipynb`) loads the processed data and generates:

- **Overview panels**: Bar charts with error bars, box plots, and scatter plots of collision metrics by model type.
- **Timeseries plots**: Per-simulation collision intensity over time.
- **X-position distributions**: Histograms of lateral cell position during active migration.
- **Statistical comparisons**: Pairwise t-tests between model types.

The cell shape visuals notebook (`03_cell_shape_visuals.ipynb`) creates high-quality spatial and temporal plots:

- **Filled Cell Snapshots**: Alpha-composited cell masks overlaid onto the physical track boundary, colored by time (viridis colormap) and smoothed with a Gaussian filter.
- **Collision Intensity**: A temporal plot of collision intensity under-filled with the corresponding viridis progression."""

new_section = """### Step 2: Visualization & Statistics

The visualization notebook (`02_visualize_results.ipynb`) loads the processed data and generates:

- **Overview panels**: Bar charts with error bars and scatter plots mapping track progress vs. mean collision intensity across the various model types, split by track geometry.

### Step 3: Cell Shape Visuals

The cell shape visuals notebook (`03_cell_shape_visuals.ipynb`) creates high-quality spatial and temporal plots overlaid directly onto the track geometry:

- **Filled Cell Snapshots**: Alpha-composited cell masks overlaid onto the physical track boundary, colored by time (viridis colormap) and smoothed with a Gaussian filter to demonstrate cell deformation along the route.
- **Collision Intensity**: A temporal plot of collision intensity under-filled with the corresponding viridis progression to show when and where the cell struggled along the track."""

if old_section in text:
    text = text.replace(old_section, new_section)
    with open("README.md", "w") as f:
        f.write(text)
    print("README updated successfully")
else:
    print("Could not find section to replace in README.md")
