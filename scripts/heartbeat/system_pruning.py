import os
import shutil

def prune():
    count = 0
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__" or d == ".pytest_cache":
                path = os.path.join(root, d)
                print(f"Borrando: {path}")
                shutil.rmtree(path, ignore_errors=True)
                count += 1
    print(f"Limpieza completada. Se eliminaron {count} directorios de caché.")

if __name__ == "__main__":
    prune()
