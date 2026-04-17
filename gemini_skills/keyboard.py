import sys
import time

def send_keys(text, window_title=None):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        if window_title:
            shell.AppActivate(window_title)
            time.sleep(0.5)
        shell.SendKeys(text)
    except Exception:
        import subprocess
        # Si falla win32com, usamos PowerShell con AppActivate
        activate_cmd = f'$wshell.AppActivate("{window_title}");' if window_title else ""
        ps_command = f'$wshell = New-Object -ComObject WScript.Shell; {activate_cmd} $wshell.SendKeys("{text}")'
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    text = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "Google Chrome" # Por defecto buscamos Chrome
    
    print(f"ACCION: Enfocando '{title}' y enviando teclas...")
    send_keys(text, title)
    print("ACCION: Teclas enviadas.")
