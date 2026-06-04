"""
Grayscale Conversion Utility
=============================

Converts PNG images to grayscale TIFF files suitable for Morpheus simulation
initialization. Supports 8-bit, 16-bit, and 32-bit output formats.

The 16-bit format is recommended for Morpheus gradient fields because it
preserves more precision than 8-bit while remaining compatible with the
TIFF reader in Morpheus.

Usage:
    # As a module
    from utils.grayscale_convert import convert_png_to_tiff
    convert_png_to_tiff("gradient.png", "gradient.tiff")

    # From command line
    python -m utils.grayscale_convert input.png output.tiff --bits 16
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def convert_png_to_tiff(
    input_path: str,
    output_path: str,
    bit_depth: int = 16,
    width: int = None,
    height: int = None,
    flip_vertical: bool = True,
    resample_method: str = 'NEAREST',
) -> str:
    """Convert a PNG image to a grayscale TIFF file.

    Args:
        input_path: Path to the input PNG image.
        output_path: Path for the output TIFF file.
        bit_depth: Output bit depth (8, 16, or 32). Default is 16.
        width: Target width in pixels (None to keep original).
        height: Target height in pixels (None to keep original).
        flip_vertical: If True, flip the image vertically to align with
            Morpheus domain coordinates (origin at bottom-left).
        resample_method: Resampling method for resize. One of 'NEAREST',
            'BOX', 'BILINEAR', 'HAMMING', 'BICUBIC', 'LANCZOS'.

    Returns:
        The output file path.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If an unsupported bit depth is specified.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load and convert to 8-bit grayscale
    img = Image.open(input_path).convert('L')

    # Resize if dimensions specified
    if width is not None and height is not None:
        resample_dict = {
            'NEAREST': Image.NEAREST,
            'BOX': Image.BOX,
            'BILINEAR': Image.BILINEAR,
            'HAMMING': Image.HAMMING,
            'BICUBIC': Image.BICUBIC,
            'LANCZOS': Image.LANCZOS,
        }
        resample = resample_dict.get(resample_method.upper(), Image.NEAREST)
        img = img.resize((width, height), resample)

    # Convert to target bit depth
    arr = np.array(img)
    if bit_depth == 8:
        img_out = Image.fromarray(arr.astype(np.uint8), mode='L')
    elif bit_depth == 16:
        # Scale 0–255 to 0–65535 to use the full 16-bit range
        arr16 = arr.astype(np.uint16) * 257
        img_out = Image.fromarray(arr16, mode='I;16')
    elif bit_depth == 32:
        arr32 = (arr.astype(np.float32) / 255.0) * (2**32 - 1)
        img_out = Image.fromarray(arr32.astype(np.uint32), mode='I')
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}. Use 8, 16, or 32.")

    # Flip vertically to match Morpheus coordinate system
    if flip_vertical:
        img_out = img_out.transpose(Image.FLIP_TOP_BOTTOM)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    img_out.save(output_path, format='TIFF')
    print(f"Saved {bit_depth}-bit TIFF: {output_path}")
    return output_path


def main():
    """Command-line entry point for grayscale conversion."""
    parser = argparse.ArgumentParser(
        description='Convert a PNG image to a grayscale TIFF for Morpheus.',
    )
    parser.add_argument('input', help='Input PNG image file')
    parser.add_argument('output', help='Output TIFF file path')
    parser.add_argument(
        '--bits', type=int, default=16, choices=[8, 16, 32],
        help='Output bit depth (default: 16)',
    )
    parser.add_argument('--width', type=int, default=None, help='Resize width')
    parser.add_argument('--height', type=int, default=None, help='Resize height')
    parser.add_argument(
        '--no-flip', action='store_true',
        help='Do not flip the image vertically',
    )
    parser.add_argument(
        '--resample', default='NEAREST',
        choices=['NEAREST', 'BOX', 'BILINEAR', 'HAMMING', 'BICUBIC', 'LANCZOS'],
        help='Resampling method for resize (default: NEAREST)',
    )
    args = parser.parse_args()

    convert_png_to_tiff(
        input_path=args.input,
        output_path=args.output,
        bit_depth=args.bits,
        width=args.width,
        height=args.height,
        flip_vertical=not args.no_flip,
        resample_method=args.resample,
    )


if __name__ == '__main__':
    main()
