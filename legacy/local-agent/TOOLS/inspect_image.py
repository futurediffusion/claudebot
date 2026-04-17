#!/usr/bin/env python3
"""
Inspect image properties (dimensions, format, mode).
"""

import sys
import os
from pathlib import Path


def inspect_image(image_path):
    """Inspect and print image properties."""
    if not os.path.exists(image_path):
        print(f"ERROR: {image_path} not found")
        sys.exit(1)

    path = Path(image_path)
    print(f"PATH: {image_path}")
    print(f"SIZE: {path.stat().st_size} bytes")

    try:
        from PIL import Image
        with Image.open(image_path) as img:
            print(f"WIDTH: {img.width}")
            print(f"HEIGHT: {img.height}")
            print(f"FORMAT: {img.format}")
            print(f"MODE: {img.mode}")
    except ImportError:
        print("NOTE: Pillow not available for detailed inspection")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_image.py <image_path>")
        sys.exit(1)

    inspect_image(sys.argv[1])