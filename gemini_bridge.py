"""
Gemini Bridge - Exclusive control center for Gemini CLI Agent.
Unifies browser-use, windows-use, and worker-core tools.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add orchestrator to path to reuse tools
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from orchestrator.tools.worker_core_bridge import (
        BrowserAutomationTool,
        WindowsAutomationTool,
        WorkerOrchestratorTool
    )
except ImportError:
    print("Error: Could not import worker-core tools. Make sure you are in the claudebot root.")
    sys.exit(1)

class GeminiBridge:
    def __init__(self):
        self.browser = BrowserAutomationTool()
        self.windows = WindowsAutomationTool()
        self.worker = WorkerOrchestratorTool()
        self.log_dir = ROOT / "gemini_memory"
        self.log_dir.mkdir(exist_ok=True)

    def log_action(self, tool_name, task, result):
        """Log actions for future session context."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d')}.jsonl"
        entry = {
            "timestamp": timestamp,
            "tool": tool_name,
            "task": task,
            "success": result.get("success", False),
            "summary": str(result.get("content", ""))[:200] if result.get("success") else result.get("error")
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def run_browser(self, task: str):
        print(f"🚀 Gemini -> Browser: {task}")
        result = self.browser.execute(task)
        self.log_action("browser", task, result)
        return result

    def run_windows(self, task: str):
        print(f"🖥️ Gemini -> Windows: {task}")
        result = self.windows.execute(task)
        self.log_action("windows", task, result)
        return result

    def run_worker(self, task: str):
        print(f"🤖 Gemini -> Worker Core: {task}")
        result = self.worker.execute(task)
        self.log_action("worker", task, result)
        return result

    def surgical_edit(self, file_path: str, old_text: str, new_text: str):
        """Gemini's signature tool: Precise text replacement."""
        print(f"✂️ Gemini -> Surgical Edit: {file_path}")
        p = Path(file_path)
        if not p.exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        content = p.read_text(encoding="utf-8")
        if old_text not in content:
            return {"success": False, "error": "Original text not found in file"}
        
        new_content = content.replace(old_text, new_text, 1) # Only one replacement for safety
        p.write_text(new_content, encoding="utf-8")
        
        result = {"success": True, "path": str(p)}
        self.log_action("surgical_edit", f"Edit {file_path}", result)
        return result

if __name__ == "__main__":
    # CLI interface for manual tests
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Bridge CLI")
    parser.add_argument("tool", choices=["browser", "windows", "worker", "edit"])
    parser.add_argument("task", help="Task or File Path")
    parser.add_argument("--old", help="Old text for edit")
    parser.add_argument("--new", help="New text for edit")
    
    args = parser.parse_args()
    bridge = GeminiBridge()
    
    if args.tool == "browser":
        print(json.dumps(bridge.run_browser(args.task), indent=2))
    elif args.tool == "windows":
        print(json.dumps(bridge.run_windows(args.task), indent=2))
    elif args.tool == "worker":
        print(json.dumps(bridge.run_worker(args.task), indent=2))
    elif args.tool == "edit":
        if not args.old or not args.new:
            print("Error: --old and --new required for edit")
        else:
            print(json.dumps(bridge.surgical_edit(args.task, args.old, args.new), indent=2))
