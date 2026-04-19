import os
import json
import sys
import glob
import fnmatch

def search_files(root_dir, pattern, recursive=True):
    """Busqueda rapida de archivos por patron de nombre"""
    matches = []
    if recursive:
        for root, dirnames, filenames in os.walk(root_dir):
            # Ignorar carpetas pesadas/basura
            if any(x in root for x in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            for filename in fnmatch.filter(filenames, pattern):
                matches.append(os.path.join(root, filename))
    else:
        for filename in fnmatch.filter(os.listdir(root_dir), pattern):
            matches.append(os.path.join(root_dir, filename))
    return matches[:50] # Limite de seguridad

def grep_content(root_dir, query_text, extension="*.py"):
    """Busca fragmentos de texto dentro de los archivos"""
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
                            results.append({
                                "file": file_path,
                                "line": line_no,
                                "content": line.strip()
                            })
            except: pass
        if len(results) > 30: break # Limite de seguridad
    return results

def get_tree(root_dir, max_depth=2):
    """Genera un mapa estructural de la carpeta"""
    tree = {}
    start_level = root_dir.count(os.sep)
    for root, dirs, files in os.walk(root_dir):
        level = root.count(os.sep) - start_level
        if level > max_depth:
            continue
        tree[root] = {"dirs": dirs, "files": files[:20]}
    return tree

def run_mcp_loop():
    print("--- FILE ORACLE MCP SERVER ONLINE ---")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            root = params.get("root", os.getcwd())
            
            if method == "search":
                result = search_files(root, params.get("pattern", "*"))
            elif method == "grep":
                result = grep_content(root, params.get("query"), params.get("ext", "*.py"))
            elif method == "tree":
                result = get_tree(root, params.get("depth", 2))
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Test: Buscando archivos '.py' en el root...")
        print(json.dumps(search_files(os.getcwd(), "*.py"), indent=2))
    else:
        run_mcp_loop()
