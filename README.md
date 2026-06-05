# Morpheus Chemotaxis Collision Analysis Pipeline

Analysis pipeline for quantifying cell-boundary collisions in Morpheus CPM (Cellular Potts Model) simulations of chemotaxis through complex track environments. Developed for the study of how different intracellular regulatory circuits (Rac frontness circuits, Rac-Rho mutual antagonism, and membrane tension feedback) affect navigation performance in confined channels with sharp turns and weak chemical gradients.

Processes simulation outputs — including cell centroid tracking, collision detection via morphological dilation, and track progress calculation — to produce summary statistics and publication-quality visualizations comparing model types.

> **Paper:** Huras E, Algorta J, De Belly H, Weiner OD, Edelstein-Keshet L. *Mechanochemical Feedback Enables Efficient Navigation in Complex Chemical Gradients.* (2026)
>
> **Models compared:** WP (Wave Pinning), WPI (WP + Inhibitor), WPI-PIP3 (WP + Inhibitor + PIP3), RacRho (Rac-Rho mutual antagonism), RacRho_T (RacRho + membrane tension feedback)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/morpheus-chemotaxis-analysis.git
cd morpheus-chemotaxis-analysis

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the analysis notebooks
cd notebooks
jupyter notebook
```

1. Open and run **`01_bulk_collision_analysis.ipynb`** — processes the sample simulation data and produces summary/detailed PKL and CSV files in `output/`.
2. Open and run **`02_visualize_results.ipynb`** — loads the processed data and generates overview plots, distribution analyses, and statistical comparisons.
3. Open and run **`03_cell_shape_visuals.ipynb`** — produces cell shape snapshots overlaid on the track boundary, and collision intensity over time colored by progress.

## Repository Structure

```
morpheus-chemotaxis-analysis/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore
│
├── data/
│   └── sample_simulations/            # Sample Morpheus output (10 simulations)
│       ├── WP_Track_.../       #   2 simulations per model type
│       ├── WPI_Track_.../      #   Each contains model.xml,
│       ├── WPIPIP3_.../       #   celltracks.xml, and plot PNGs
│       ├── RacRho_.../
│       └── RacRho_T_.../
│
├── morpheus_files/                    # Place Morpheus model XMLs here
│
├── utils/                             # Reusable analysis modules
│   ├── __init__.py
│   ├── image_processing.py            # Color detection, collision, centroid
│   ├── simulation_parser.py           # XML parsing, PNG discovery
│   ├── grayscale_convert.py           # PNG → TIFF gradient preparation
│   └── isoline_generator.py           # Contour visualization
│
├── notebooks/                         # Analysis notebooks
│   ├── 01_bulk_collision_analysis.ipynb
│   ├── 02_visualize_results.ipynb
│   └── 03_cell_shape_visuals.ipynb
│
└── output/                            # Generated results (gitignored)
```

## Pipeline Overview

```
Simulation Folders                     Analysis Output
┌──────────────────────┐               ┌──────────────────────┐
│ model.xml            │──► Parse ──►  │ collision_analysis_   │
│ celltracks.xml       │   metadata    │ summary.csv           │
│ plot_*.png           │               │   (1 row/simulation)  │
└──────────────────────┘               │                       │
         │                             │ collision_analysis_   │
         ▼                             │ detailed.csv          │
┌──────────────────────┐               │   (1 row/frame)       │
│ Cell Detection       │               └──────────┬───────────┘
│  ├ Black pixel mask  │                          │
│  ├ 3×3 dilation      │                          ▼
│  └ Green overlap     │──► Collision   ┌──────────────────────┐
└──────────────────────┘    metrics     │ Visualizations       │
                                        │  ├ Overview panels   │
                                        │  ├ Box plots         │
                                        │  ├ Scatter plots     │
                                        │  └ t-test tables     │
                                        └──────────────────────┘
```

### Step 1: Bulk Collision Analysis

The processing notebook (`01_bulk_collision_analysis.ipynb`) iterates over simulation folders and for each one:

1. **Parses `model.xml`** to extract domain dimensions, track type, gradient parameters, and simulation duration.
2. **Extracts cell trajectories** from `celltracks.xml` (preferred) or falls back to image-based centroid detection using black pixel segmentation.
3. **Discovers PNG frames** by testing naming patterns (`plot_`, `plot-1_`, etc.) and validating color content.
4. **Detects collisions** per frame by dilating the cell body mask (3×3 kernel, equivalent to checking the 8-pixel neighborhood) and checking overlap with green boundary pixels. A collision occurs when any pixel of the cell's perimeter is adjacent to a track boundary pixel.
5. **Computes summary metrics**: collision percentage (fraction of frames with ≥1 collision), collision intensity (collision pixels / total boundary pixels), and track progress (max Y-position / domain height).

### Step 2: Visualization & Statistics

The visualization notebook (`02_visualize_results.ipynb`) loads the processed data and generates:

- **Overview panels**: Bar charts with error bars, box plots, and scatter plots of collision metrics by model type.
- **Timeseries plots**: Per-simulation collision intensity over time.
- **X-position distributions**: Histograms of lateral cell position during active migration.
- **Statistical comparisons**: Pairwise t-tests between model types.

The cell shape visuals notebook (`03_cell_shape_visuals.ipynb`) creates high-quality spatial and temporal plots:

- **Filled Cell Snapshots**: Alpha-composited cell masks overlaid onto the physical track boundary, colored by time (viridis colormap) and smoothed with a Gaussian filter.
- **Collision Intensity**: A temporal plot of collision intensity under-filled with the corresponding viridis progression.

## Using Your Own Data

To analyze your own Morpheus simulation outputs:

1. Organize your simulation folders in a single directory. Each subfolder should contain at minimum:
   - `model.xml` — Morpheus simulation configuration
   - `plot_*.png` — Visualization output frames
   - `celltracks.xml` — Cell tracking data (optional but recommended)

2. In `01_bulk_collision_analysis.ipynb`, update the configuration cell:
   ```python
   DATA_DIR = "/path/to/your/simulation/folders"
   EXCLUDE_SIMULATION_IDS = ['bad_sim_1', 'bad_sim_2']  # if any
   ```

3. Run both notebooks in order.

### Folder Naming Convention

The pipeline extracts model type and simulation ID from folder names following the pattern:
```
{Prefix}_{ModelType}_{Rest}_{SimulationID}
```
For example:
- `WP_Track_Collision_TrackB_1` → Model: `WP`, ID: `1`
- `RacRho_Collision_TrackB_1759` → Model: `RacRho`, ID: `1759`

## Utility Scripts

### Grayscale Converter

Converts PNG images to grayscale TIFF files for Morpheus gradient field initialization:

```bash
python -m utils.grayscale_convert input.png output.tiff --bits 16 --width 300 --height 450
```

### Isoline Generator

Overlays contour lines on gradient images for visualization:

```bash
python -m utils.isoline_generator gradient.png output.png --levels 12 --color red
```

## Image Format

Morpheus outputs 24-bit RGB PNG images with the following color encoding:

| Feature        | RGB Value     | Detection Tolerance |
|----------------|---------------|---------------------|
| Cell body      | (0, 0, 0)     | ±10 per channel     |
| Track boundary  | (0, 255, 0)   | ±50 per channel     |
| Track path      | (255, 255, 255) | > 200 (validation) |

## Dependencies

| Package         | Minimum Version | Purpose                        |
|-----------------|-----------------|--------------------------------|
| Python          | 3.9+            | Runtime                        |
| NumPy           | 1.19.0          | Array operations               |
| Pandas          | 1.3.0           | DataFrames and I/O             |
| OpenCV          | 4.5.0           | Image segmentation             |
| Matplotlib      | 3.3.0           | Plotting                       |
| Seaborn         | 0.11.0          | Statistical visualization      |
| SciPy           | 1.5.0           | Statistical tests, smoothing   |
| Pillow          | 8.0.0           | Image format conversion        |

## License

*[To be added]*

## Citation

If you use this pipeline in your work, please cite:

```
Huras E, Algorta J, De Belly H, Weiner OD, Edelstein-Keshet L.
Mechanochemical Feedback Enables Efficient Navigation in Complex Chemical Gradients.
(2026)
```
