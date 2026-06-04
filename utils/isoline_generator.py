"""
Isoline Generator
==================

Generates contour lines (isolines) on gradient images for visualizing
chemoattractant fields used in Morpheus simulations.

Usage:
    # As a module
    from utils.isoline_generator import generate_isolines
    generate_isolines("gradient.png", "output.png", num_levels=12)

    # From command line
    python -m utils.isoline_generator input.png output.png --levels 20
"""

import argparse
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


def generate_isolines(
    input_path: str,
    output_path: str,
    num_levels: int = 12,
    line_color: str = 'red',
    line_width: float = 2.0,
    show_original: bool = True,
    smooth_sigma: float = 2.0,
    exclude_edges: bool = True,
    edge_percentile: float = 5.0,
) -> bool:
    """Generate contour lines from a grayscale gradient image.

    Loads a grayscale image, applies Gaussian smoothing, then overlays
    evenly-spaced contour lines. Edge percentile exclusion avoids thick
    contour lines along image boundaries.

    Args:
        input_path: Path to input image (PNG or TIFF).
        output_path: Path to save the output image.
        num_levels: Number of contour lines to draw.
        line_color: Matplotlib color for contour lines.
        line_width: Width of contour lines.
        show_original: If True, display the original image behind contours.
        smooth_sigma: Gaussian smoothing sigma for smoother contours.
        exclude_edges: If True, exclude extreme intensity values.
        edge_percentile: Percentile to exclude from each edge of the
            intensity range (e.g., 5 excludes the bottom and top 5%).

    Returns:
        True if successful, False otherwise.
    """
    try:
        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' not found.")
            return False

        img = Image.open(input_path)
        if img.mode != 'L':
            img = img.convert('L')

        img_array = np.array(img, dtype=float)
        print(f"Image: {img_array.shape[1]}x{img_array.shape[0]}, "
              f"range [{img_array.min():.0f}, {img_array.max():.0f}]")

        # Gaussian smoothing for clean contours
        from scipy.ndimage import gaussian_filter
        img_smoothed = gaussian_filter(img_array, sigma=smooth_sigma)

        # Set up a figure matching the image dimensions
        dpi = 100
        height, width = img_array.shape
        fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)

        # Background
        if show_original:
            ax.imshow(img_array, cmap='gray', aspect='auto',
                      interpolation='bilinear')
        else:
            ax.imshow(np.ones_like(img_array) * 255, cmap='gray', aspect='auto')

        # Contour levels
        if exclude_edges:
            min_val = np.percentile(img_smoothed, edge_percentile)
            max_val = np.percentile(img_smoothed, 100 - edge_percentile)
        else:
            min_val = img_smoothed.min()
            max_val = img_smoothed.max()

        levels = np.linspace(min_val, max_val, num_levels)
        ax.contour(img_smoothed, levels=levels, colors=line_color,
                   linewidths=line_width, antialiased=True)

        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight',
                    pad_inches=0, facecolor='white', edgecolor='none')
        plt.close()

        print(f"Isolines saved to: {output_path}")
        return True

    except ImportError:
        print("Missing scipy. Install with: pip install scipy")
        return False
    except Exception as e:
        print(f"Error generating isolines: {e}")
        return False


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Generate isolines (contour lines) on a gradient image.',
    )
    parser.add_argument('input', help='Input image file (PNG or TIFF)')
    parser.add_argument('output', help='Output PNG file')
    parser.add_argument('-l', '--levels', type=int, default=12,
                        help='Number of contour lines (default: 12)')
    parser.add_argument('-c', '--color', default='red',
                        help='Contour line color (default: red)')
    parser.add_argument('-w', '--width', type=float, default=2.0,
                        help='Contour line width (default: 2.0)')
    parser.add_argument('-s', '--smooth', type=float, default=2.0,
                        help='Gaussian smoothing sigma (default: 2.0)')
    parser.add_argument('--edge-percentile', type=float, default=5.0,
                        help='Edge exclusion percentile (default: 5.0)')
    parser.add_argument('--no-original', action='store_true',
                        help='Hide the original image behind contours')
    parser.add_argument('--include-edges', action='store_true',
                        help='Include edge contours (not recommended)')
    args = parser.parse_args()

    success = generate_isolines(
        input_path=args.input,
        output_path=args.output,
        num_levels=args.levels,
        line_color=args.color,
        line_width=args.width,
        show_original=not args.no_original,
        smooth_sigma=args.smooth,
        exclude_edges=not args.include_edges,
        edge_percentile=args.edge_percentile,
    )
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
