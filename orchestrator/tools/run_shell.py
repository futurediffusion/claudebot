"""
Shell execution tool.
"""

import subprocess
import shutil
from typing import Dict, Any, Optional


class RunShellTool:
    """Execute shell commands safely."""

    def __init__(self):
        self.supported_shells = ["bash", "sh", "cmd", "powershell"]

    def is_available(self, shell: str = "bash") -> bool:
        """Check if shell is available."""
        return shutil.which(shell) is not None

    def execute(
        self,
        command: str,
        shell: str = "bash",
        timeout: int = 30,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }

    def execute_bat(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a Windows batch command."""
        return self.execute(command, shell="cmd", timeout=timeout)