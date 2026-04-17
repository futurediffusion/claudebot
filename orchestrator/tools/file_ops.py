"""
File operations tool - read, write, list, search.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class FileOpsTool:
    """Basic file operations."""

    def read(self, path: str) -> Dict[str, Any]:
        """Read file contents."""
        try:
            p = Path(path)
            if not p.exists():
                return {"success": False, "error": "File not found", "content": ""}

            content = p.read_text(encoding="utf-8")
            return {"success": True, "content": content, "path": str(p)}
        except Exception as e:
            return {"success": False, "error": str(e), "content": ""}

    def write(self, path: str, content: str) -> Dict[str, Any]:
        """Write file contents."""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(p)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_dir(self, path: str, pattern: Optional[str] = None) -> Dict[str, Any]:
        """List directory contents."""
        try:
            p = Path(path)
            if not p.exists() or not p.is_dir():
                return {"success": False, "error": "Invalid directory", "files": []}

            items = list(p.iterdir())
            files = [str(item) for item in items]

            if pattern:
                files = [f for f in files if pattern in f]

            return {"success": True, "files": files, "path": str(p)}
        except Exception as e:
            return {"success": False, "error": str(e), "files": []}

    def search(self, directory: str, pattern: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for files matching pattern."""
        try:
            p = Path(directory)
            if not p.exists():
                return {"success": False, "error": "Directory not found", "matches": []}

            matches = []
            for fp in p.rglob("*"):
                if fp.is_file():
                    name = fp.name
                    if pattern in name:
                        if extensions is None or any(name.endswith(ext) for ext in extensions):
                            matches.append(str(fp))

            return {"success": True, "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e), "matches": []}

    def glob(self, directory: str, pattern: str) -> Dict[str, Any]:
        """Glob pattern matching."""
        try:
            p = Path(directory)
            matches = list(p.glob(pattern))
            return {"success": True, "matches": [str(m) for m in matches]}
        except Exception as e:
            return {"success": False, "error": str(e), "matches": []}