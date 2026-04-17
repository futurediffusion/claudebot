"""
Screenshot tool - capture screen for vision model analysis.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional


class ScreenshotTool:
    """Capture screenshots for vision analysis."""

    def capture(
        self,
        output_path: Optional[str] = None,
        region: Optional[tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Capture a screenshot.

        Args:
            output_path: Optional path to save the screenshot
            region: Optional (x, y, width, height) for partial capture

        Returns:
            Dict with success, path, and base64 data
        """
        try:
            # Try using various screenshot methods
            from PIL import ImageGrab

            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()

            # Generate output path if not provided
            if not output_path:
                output_path = f"screenshot_{os.getpid()}.png"

            screenshot.save(output_path)

            # Read and encode for vision model
            with open(output_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()

            return {
                "success": True,
                "path": output_path,
                "base64": data,
                "size": os.path.getsize(output_path)
            }
        except ImportError:
            # PIL not available
            return {
                "success": False,
                "error": "PIL/Pillow not available for screenshots",
                "path": None,
                "base64": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": None,
                "base64": None
            }

    def load_existing(self, path: str) -> Dict[str, Any]:
        """Load an existing image file."""
        try:
            p = Path(path)
            if not p.exists():
                return {"success": False, "error": "File not found"}

            with open(p, "rb") as f:
                data = base64.b64encode(f.read()).decode()

            return {
                "success": True,
                "path": str(p),
                "base64": data,
                "size": p.stat().st_size
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cleanup(self, path: str) -> Dict[str, Any]:
        """Remove a screenshot file."""
        try:
            p = Path(path)
            if p.exists():
                p.unlink()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}