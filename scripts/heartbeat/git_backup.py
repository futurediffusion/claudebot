import subprocess
from datetime import datetime

def run():
    try:
        # Añadir cambios
        subprocess.run(["git", "add", "."], check=True)
        # Commit con timestamp
        msg = f"chore: automated heartbeat backup {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        print("Backup completado.")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e.output) or e.returncode == 1:
            print("Nada nuevo que commitear.")
        else:
            raise e

if __name__ == "__main__":
    run()
