import os
import fnmatch
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file-oracle")


def _search_files(root_dir, pattern, recursive=True):
    matches = []
    if recursive:
        for root, dirnames, filenames in os.walk(root_dir):
            if any(x in root for x in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            for filename in fnmatch.filter(filenames, pattern):
                matches.append(os.path.join(root, filename))
    else:
        for filename in fnmatch.filter(os.listdir(root_dir), pattern):
            matches.append(os.path.join(root_dir, filename))
    return matches[:50]


def _grep_content(root_dir, query_text, extension="*.py"):
    results = []
    for root, dirnames, filenames in os.walk(root_dir):
        if any(x in root for x in ['.git', '__pycache__', 'node_modules', 'venv']):
            continue
        for filename in fnmatch.filter(filenames, extension):
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_no, line in enumerate(f, 1):
                        if query_text.lower() in line.lower():
                            results.append({"file": file_path, "line": line_no, "content": line.strip()})
            except:
                pass
        if len(results) > 30:
            break
    return results


def _get_tree(root_dir, max_depth=2):
    tree = {}
    start_level = root_dir.count(os.sep)
    for root, dirs, files in os.walk(root_dir):
        level = root.count(os.sep) - start_level
        if level > max_depth:
            continue
        tree[root] = {"dirs": dirs, "files": files[:20]}
    return tree


@mcp.tool()
def search_files(root_dir: str, pattern: str, recursive: bool = True) -> list:
    """Busca archivos por patrón de nombre (ej: '*.py'). Máx 50 resultados."""
    return _search_files(root_dir, pattern, recursive)


@mcp.tool()
def grep_content(root_dir: str, query: str, extension: str = "*.py") -> list:
    """Busca texto dentro de archivos. Devuelve archivo, línea y contenido."""
    return _grep_content(root_dir, query, extension)


@mcp.tool()
def get_tree(root_dir: str, max_depth: int = 2) -> dict:
    """Genera mapa estructural de una carpeta hasta max_depth niveles."""
    return _get_tree(root_dir, max_depth)


if __name__ == "__main__":
    mcp.run()
