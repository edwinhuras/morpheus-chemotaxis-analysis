"""
Image Processing Utilities for Morpheus Simulation Analysis
============================================================

Functions for color-based segmentation, collision detection, and cell centroid
extraction from Morpheus CPM simulation output images.

Morpheus outputs PNG images where:
- Black pixels (RGB ~0,0,0) represent the cell body
- Green pixels (RGB ~0,255,0) represent maze boundaries
- White pixels (RGB ~255,255,255) represent open maze paths
"""

import numpy as np
import cv2
from typing import Tuple


def load_color_image(filepath: str) -> np.ndarray:
    """Load an image in BGR color format (OpenCV convention).

    Args:
        filepath: Path to the PNG image file.

    Returns:
        NumPy array of shape (H, W, 3) in BGR format.

    Raises:
        ValueError: If the image could not be loaded.
    """
    img = cv2.imread(filepath)
    if img is None:
        raise ValueError(f"Could not load image: {filepath}")
    return img


def analyze_png_colors(filepath: str) -> Tuple[float, float, bool]:
    """Analyze a PNG's color content to verify it is a valid simulation frame.

    Checks for expected proportions of white (maze path) and green (boundary)
    pixels. A valid frame has >30% white and >1% green.

    Args:
        filepath: Path to the PNG file.

    Returns:
        Tuple of (white_ratio, green_ratio, is_valid_frame).
    """
    try:
        img = cv2.imread(filepath)
        if img is None:
            return 0.0, 0.0, False

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        total_pixels = rgb_img.shape[0] * rgb_img.shape[1]

        # White pixels: all channels > 200
        white_mask = np.all(rgb_img > 200, axis=2)
        white_ratio = np.sum(white_mask) / total_pixels

        # Green pixels: high G, low R and B
        green_mask = (
            (rgb_img[:, :, 1] > 100)
            & (rgb_img[:, :, 0] < 100)
            & (rgb_img[:, :, 2] < 100)
        )
        green_ratio = np.sum(green_mask) / total_pixels

        is_valid = white_ratio > 0.3 and green_ratio > 0.01
        return white_ratio, green_ratio, is_valid

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return 0.0, 0.0, False


def detect_black_pixels(
    image: np.ndarray,
    tolerance: int = 10,
    border_exclude: int = 1,
) -> np.ndarray:
    """Create a binary mask of cell body (black) pixels.

    Args:
        image: BGR image array.
        tolerance: Maximum channel value to count as black (default ±10).
        border_exclude: Pixels to zero out along each image edge to avoid
            border artifacts.

    Returns:
        Binary mask (uint8) where cell pixels are 255, background is 0.
    """
    lower = np.array([0, 0, 0])
    upper = np.array([tolerance, tolerance, tolerance])
    black_mask = cv2.inRange(image, lower, upper)

    if border_exclude > 0:
        h, w = black_mask.shape
        black_mask[:border_exclude, :] = 0
        black_mask[-border_exclude:, :] = 0
        black_mask[:, :border_exclude] = 0
        black_mask[:, -border_exclude:] = 0

    return black_mask


def detect_green_pixels(
    image: np.ndarray,
    tolerance: int = 50,
) -> np.ndarray:
    """Create a binary mask of maze boundary (green) pixels.

    Args:
        image: BGR image array.
        tolerance: Color matching tolerance around pure green (default ±50).

    Returns:
        Binary mask (uint8) where boundary pixels are 255, background is 0.
    """
    # Target is pure green in BGR: (0, 255, 0)
    lower = np.array([max(0, 0 - tolerance),
                      max(0, 255 - tolerance),
                      max(0, 0 - tolerance)])
    upper = np.array([min(255, 0 + tolerance),
                      min(255, 255 + tolerance),
                      min(255, 0 + tolerance)])
    return cv2.inRange(image, lower, upper)


def detect_collision(image: np.ndarray) -> bool:
    """Check whether the cell is touching a maze boundary.

    Dilates the cell mask by 1 pixel (3×3 kernel) to detect adjacency,
    then checks for overlap with the boundary mask.

    Args:
        image: BGR color image.

    Returns:
        True if any collision pixels exist, False otherwise.
    """
    _, _, collision_count = get_collision_intensity(image)
    return collision_count > 0


def get_collision_intensity(
    image: np.ndarray,
    black_tolerance: int = 10,
    green_tolerance: int = 50,
    border_exclude: int = 1,
) -> Tuple[bool, float, int]:
    """Compute collision metrics between cell and maze boundary.

    The cell mask is dilated by 1 pixel (3×3 kernel, 1 iteration) to detect
    adjacency. Collision intensity is defined as the fraction of total boundary
    pixels that overlap with the dilated cell mask.

    Args:
        image: BGR color image.
        black_tolerance: Tolerance for cell detection.
        green_tolerance: Tolerance for boundary detection.
        border_exclude: Border pixels to exclude from cell mask.

    Returns:
        Tuple of (collision_occurred, collision_intensity, collision_pixel_count).
        Intensity is in range [0, 1] and represents the fraction of boundary
        pixels in contact with the cell.
    """
    black_mask = detect_black_pixels(image, black_tolerance, border_exclude)
    green_mask = detect_green_pixels(image, green_tolerance)

    kernel = np.ones((3, 3), np.uint8)
    dilated_black = cv2.dilate(black_mask, kernel, iterations=1)

    collision_pixels = cv2.bitwise_and(dilated_black, green_mask)
    collision_count = int(np.sum(collision_pixels == 255))
    green_count = int(np.sum(green_mask == 255))

    intensity = (collision_count / green_count) if green_count > 0 else 0.0
    return collision_count > 0, intensity, collision_count


def get_cell_centroid(
    image: np.ndarray,
    border_exclude: int = 5,
) -> Tuple[int, int]:
    """Calculate the centroid of the cell in domain coordinates.

    Domain coordinates have (0, 0) at the bottom-left corner, with Y
    increasing upward. This matches the coordinate system used in
    celltracks.xml.

    Args:
        image: BGR color image.
        border_exclude: Pixels to exclude from each edge when finding the cell.

    Returns:
        (x, y) centroid position in domain coordinates.
        Returns (0, 0) if no cell pixels are found.
    """
    black_mask = detect_black_pixels(image, border_exclude=border_exclude)
    black_pixels = np.where(black_mask == 255)

    if len(black_pixels[0]) == 0:
        return (0, 0)

    # black_pixels[0] = row indices (y in image coords, 0 = top)
    # black_pixels[1] = col indices (x in image coords, 0 = left)
    centroid_y_image = int(np.mean(black_pixels[0]))
    centroid_x_image = int(np.mean(black_pixels[1]))

    # Convert to domain coordinates: flip Y axis
    image_height = image.shape[0]
    centroid_x = centroid_x_image
    centroid_y = image_height - centroid_y_image

    return (centroid_x, centroid_y)
