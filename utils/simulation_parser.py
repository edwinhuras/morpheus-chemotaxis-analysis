"""
Simulation Data Parsing Utilities
==================================

Functions for extracting metadata and tracking data from Morpheus simulation
output folders. Each simulation folder typically contains:
- model.xml      — Simulation configuration (domain size, gradient, etc.)
- celltracks.xml — Cell centroid trajectories over time
- plot_*.png     — Visualization frames of the cell in the track
"""

import os
import re
import xml.etree.ElementTree as ET
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .image_processing import analyze_png_colors


# ---------------------------------------------------------------------------
# XML Parsing
# ---------------------------------------------------------------------------

def parse_model_xml(model_path: str) -> Dict[str, Any]:
    """Extract simulation metadata from a Morpheus model.xml file.

    Parses domain dimensions, track type, gradient parameters, and MCS duration
    from the XML configuration used to run the simulation.

    Args:
        model_path: Path to the model.xml file.

    Returns:
        Dictionary with keys:
            - width, height: Domain dimensions (strings, as parsed)
            - domain_file: Filename of the domain image
            - track_type: Cleaned track type name
            - gradient_file: Filename of the gradient TIFF
            - gradient_scale: Scaling factor for the gradient field
            - mcs_duration: Monte Carlo Sampler duration (float or None)
    """
    result = {
        'width': '',
        'height': '',
        'domain_file': '',
        'track_type': '',
        'gradient_file': '',
        'gradient_scale': 1.0,
        'mcs_duration': None,
    }

    if not os.path.exists(model_path):
        return result

    try:
        tree = ET.parse(model_path)
        root = tree.getroot()

        # Domain dimensions from <Space/Lattice/Size value="W, H, ...">
        size_elem = root.find('.//Space/Lattice/Size')
        if size_elem is not None and 'value' in size_elem.attrib:
            parts = [p.strip() for p in size_elem.attrib['value'].split(',')]
            if len(parts) >= 2:
                result['width'], result['height'] = parts[0], parts[1]

        # Domain image from <Space/Lattice/Domain/Image path="...">
        image_elem = root.find('.//Space/Lattice/Domain/Image')
        if image_elem is not None and 'path' in image_elem.attrib:
            result['domain_file'] = image_elem.attrib['path']
            domain_base = os.path.splitext(result['domain_file'])[0]
            track_type = domain_base.replace('_domain', '').replace('domain_', '')
            result['track_type'] = track_type.replace('Domain', '').strip('_')

        # Gradient field from <Field[@symbol="U"]/TIFFReader>
        tiff_reader = root.find('.//Field[@symbol="U"]/TIFFReader')
        if tiff_reader is not None:
            result['gradient_file'] = tiff_reader.attrib.get('filename', '')
            try:
                result['gradient_scale'] = float(
                    tiff_reader.attrib.get('scaling', '1.0')
                )
            except (ValueError, TypeError):
                result['gradient_scale'] = 1.0

        # MCS duration from <CPM/MonteCarloSampler/MCSDuration>
        mcs_elem = root.find('.//CPM/MonteCarloSampler/MCSDuration')
        if mcs_elem is not None and 'value' in mcs_elem.attrib:
            try:
                result['mcs_duration'] = float(mcs_elem.attrib['value'])
            except (ValueError, TypeError):
                pass

    except ET.ParseError as e:
        print(f"  XML parse error in {model_path}: {e}")

    return result


def parse_celltracks_centroids(
    celltracks_path: str,
) -> List[Tuple[int, float, float]]:
    """Parse cell centroid trajectories from celltracks.xml.

    Supports both XML structures used by Morpheus:
    - <track><spot t="..." x="..." y="..."/></track>
    - <particle><detection t="..." x="..." y="..."/></particle>

    Args:
        celltracks_path: Path to celltracks.xml.

    Returns:
        List of (timestep, x, y) tuples sorted by timestep.
    """
    centroids = []
    try:
        tree = ET.parse(celltracks_path)
        root = tree.getroot()

        # Try <track><spot .../> format
        found = False
        for track in root.findall('.//track'):
            for spot in track.findall('spot'):
                t = int(spot.attrib['t'])
                x = float(spot.attrib['x'])
                y = float(spot.attrib['y'])
                centroids.append((t, x, y))
                found = True

        # Fall back to <particle><detection .../> format
        if not found:
            for particle in root.findall('.//particle'):
                for det in particle.findall('detection'):
                    t = int(det.attrib['t'])
                    x = float(det.attrib['x'])
                    y = float(det.attrib['y'])
                    centroids.append((t, x, y))

    except Exception as e:
        print(f"  Error parsing celltracks.xml: {e}")

    centroids.sort(key=lambda tup: tup[0])
    return centroids


# ---------------------------------------------------------------------------
# PNG File Discovery
# ---------------------------------------------------------------------------

def find_correct_png_pattern(data_folder: str, verbose: bool = False) -> str:
    """Determine the correct PNG naming pattern in a simulation folder.

    Morpheus can output frames with different prefixes (plot_, plot-1_,
    plot-2_, plot-3_). This function samples files from each pattern and
    validates them by checking color content (must contain white track paths
    and green boundaries).

    Args:
        data_folder: Path to the simulation output folder.
        verbose: If True, print detailed analysis for each pattern.

    Returns:
        The correct pattern prefix string (e.g., 'plot_').
    """
    data_path = Path(data_folder)
    if not data_path.exists():
        raise FileNotFoundError(f"Data folder not found: {data_folder}")

    patterns = ['plot_', 'plot-1_', 'plot-2_', 'plot-3_']

    for pattern in patterns:
        sample_files = list(data_path.glob(f"{pattern}*.png"))
        if not sample_files:
            continue

        # Check up to 2 samples for speed
        correct_count = 0
        for sample_file in sample_files[:2]:
            _, _, is_correct = analyze_png_colors(str(sample_file))
            if is_correct:
                correct_count += 1
            if verbose:
                print(f"    {sample_file.name}: valid={is_correct}")

        if correct_count > 0:
            if verbose:
                print(f"  Selected pattern: '{pattern}'")
            return pattern

    return 'plot_'  # fallback


def find_simulation_pngs(
    data_folder: str, verbose: bool = False
) -> List[Tuple[int, str]]:
    """Find and sort all simulation frame PNGs in a folder.

    Automatically detects the correct naming pattern, then extracts the
    timestep number from each matching filename.

    Args:
        data_folder: Path to the simulation output folder.
        verbose: If True, print discovery details.

    Returns:
        List of (timestep, filepath) tuples sorted chronologically.
    """
    pattern_prefix = find_correct_png_pattern(data_folder, verbose=verbose)
    data_path = Path(data_folder)
    regex = re.compile(rf'{re.escape(pattern_prefix)}(\d+)\.png$')

    png_files = []
    for file_path in data_path.glob(f"{pattern_prefix}*.png"):
        match = regex.match(file_path.name)
        if match:
            timestep = int(match.group(1))
            png_files.append((timestep, str(file_path)))

    png_files.sort(key=lambda x: x[0])

    if verbose:
        print(f"Found {len(png_files)} PNGs with pattern '{pattern_prefix}'")

    return png_files


# ---------------------------------------------------------------------------
# Folder Name Parsing
# ---------------------------------------------------------------------------

def extract_simulation_id(folder_name: str) -> Optional[str]:
    """Extract the numeric simulation ID from a folder name.

    Handles naming conventions like:
    - WP_Track_Collision_TrackB_1
    - RacRho_Collision_TrackB_1759

    Args:
        folder_name: Base name of the simulation folder.

    Returns:
        Simulation ID string, or the full folder name if no ID is found.
    """
    match = re.search(r'(\d+)(?:\s*copy)?$', folder_name)
    return match.group(1) if match else folder_name


def extract_model_type(folder_name: str, expected_models: list) -> str:
    """Extract the model type from a simulation folder name.

    Parses folder names by splitting on underscores and checking against expected models.
    For example:
        WP_Track_Collision_TrackB_1  →  WP
        Rac-Rho_Collision_...        →  Rac-Rho
        Figure6_WPIPIP3_Collision   →  WPIPIP3

    Args:
        folder_name: Base name of the simulation folder.
        expected_models: List of expected model strings to search for.

    Returns:
        Model type string, or the first part of the folder name if not found.
    """
    parts = folder_name.split('_')
    
    for model in expected_models:
        if model in parts:
            return model
            
    # Default fallback
    default_model = parts[0] if parts else ''
    print(f"  Warning: No expected model found in '{folder_name}'. Defaulting to '{default_model}'.")
    return default_model


# ---------------------------------------------------------------------------
# Track Type Fallback
# ---------------------------------------------------------------------------

def extract_track_type_from_tiffs(folder_path: str) -> str:
    """Attempt to extract track type from TIFF filenames as a fallback.

    Used when model.xml does not contain domain information.

    Args:
        folder_path: Path to the simulation folder.

    Returns:
        Track type string, or empty string if not found.
    """
    tiff_files = glob(os.path.join(folder_path, '*.tiff'))

    # Try domain files first
    for tiff in tiff_files:
        tiff_base = os.path.basename(tiff)
        if 'domain' in tiff_base.lower():
            base = os.path.splitext(tiff_base)[0]
            track_type = base.replace('_domain', '').replace('domain_', '')
            return track_type.replace('Domain', '').strip('_')

    # Fall back to any TIFF file
    for tiff in tiff_files:
        base = os.path.splitext(os.path.basename(tiff))[0]
        cleaned = base.replace('_gradient', '').replace('gradient_', '')
        cleaned = cleaned.replace('_field', '').replace('field_', '')
        cleaned = cleaned.replace('Gradient', '').replace('Field', '')
        cleaned = cleaned.strip('_')
        if cleaned:
            return cleaned

    return ''


# ---------------------------------------------------------------------------
# Progress Calculation
# ---------------------------------------------------------------------------

def get_progress_from_centroids(
    centroids: List[Tuple[int, float, float]],
    domain_height: Any,
) -> Tuple[float, float]:
    """Compute track progress from centroid trajectory.

    Progress is defined as the maximum Y-coordinate reached divided by the
    domain height, expressed as a percentage.

    Args:
        centroids: List of (timestep, x, y) centroid positions.
        domain_height: Domain height (will be converted to float).

    Returns:
        Tuple of (max_y_position, track_progress_percentage).
    """
    if not centroids or not domain_height:
        return 0.0, 0.0
    try:
        height = float(domain_height)
    except (ValueError, TypeError):
        return 0.0, 0.0

    max_y = max(y for _, _, y in centroids)
    progress = (max_y / height) * 100 if height > 0 else 0.0
    return max_y, progress
