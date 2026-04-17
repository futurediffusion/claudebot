"""
Gemini bridge for browser-use, windows-use, and worker-core.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ORCHESTRATOR_ROOT = ROOT / "orchestrator"
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

try:
    from core.self_model_engine import SelfModelEngine
    from orchestrator.tools.worker_core_bridge import (
        BrowserAutomationTool,
        WindowsAutomationTool,
        WorkerOrchestratorTool,
    )
except ImportError:
    print("Error: Could not import worker-core tools. Make sure you are in the claudebot root.")
    sys.exit(1)


class GeminiBridge:
    def __init__(self):
        self.browser = BrowserAutomationTool()
        self.windows = WindowsAutomationTool()
        self.worker = WorkerOrchestratorTool()
        self.self_model = SelfModelEngine(agent_name="gemini_cli")
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
            "summary": str(result.get("content", ""))[:200] if result.get("success") else result.get("error"),
        }
        with open(log_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def _record_self_model(self, tool_name, task, result):
        """Update the shared self-model from Gemini executions."""
        model_map = {
            "browser": ("worker-core:browser", "browser_automation"),
            "windows": ("worker-core:windows", "windows_automation"),
            "worker": ("worker-core:orchestrator", "worker_automation"),
            "surgical_edit": ("gemini:surgical_edit", "file_edit"),
        }
        model_name, task_type = model_map[tool_name]
        self.self_model.record_execution(
            task=task,
            task_type=task_type,
            model_name=model_name,
            success=result.get("success", False),
            execution_time_ms=0,
            error=result.get("error"),
            tools_used=[tool_name],
            metadata={"source": "gemini_bridge"},
        )

    def run_browser(self, task: str):
        print(f"Gemini -> Browser: {task}")
        result = self.browser.execute(task)
        self.log_action("browser", task, result)
        self._record_self_model("browser", task, result)
        return result

    def run_windows(self, task: str):
        print(f"Gemini -> Windows: {task}")
        result = self.windows.execute(task)
        self.log_action("windows", task, result)
        self._record_self_model("windows", task, result)
        return result

    def run_worker(self, task: str):
        print(f"Gemini -> Worker Core: {task}")
        result = self.worker.execute(task)
        self.log_action("worker", task, result)
        self._record_self_model("worker", task, result)
        return result

    def run_auto(self, task: str):
        """Use the self-model to choose the best Gemini entrypoint."""
        tool_plan = self.self_model.suggest_tool(
            task,
            available_tools=["browser", "windows", "worker", "surgical_edit"],
        )
        selected_tool = tool_plan.get("selected_tool", "worker")

        if selected_tool == "browser":
            return self.run_browser(task)
        if selected_tool == "windows":
            return self.run_windows(task)
        if selected_tool == "worker":
            return self.run_worker(task)

        return {
            "success": False,
            "error": "Self-model selected surgical_edit, but auto mode needs explicit file arguments.",
            "self_model": tool_plan,
        }

    def surgical_edit(self, file_path: str, old_text: str, new_text: str):
        """Gemini's signature tool: precise text replacement."""
        print(f"Gemini -> Surgical Edit: {file_path}")
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File {file_path} not found"}

        content = path.read_text(encoding="utf-8")
        if old_text not in content:
            return {"success": False, "error": "Original text not found in file"}

        new_content = content.replace(old_text, new_text, 1)
        path.write_text(new_content, encoding="utf-8")

        result = {"success": True, "path": str(path)}
        self.log_action("surgical_edit", f"Edit {file_path}", result)
        self._record_self_model("surgical_edit", f"Edit {file_path}", result)
        return result

    def summary(self):
        """Return the shared self-model summary as seen by Gemini."""
        return self.self_model.get_summary()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Bridge CLI")
    parser.add_argument("tool", choices=["browser", "windows", "worker", "auto", "edit", "summary"])
    parser.add_argument("task", nargs="?", help="Task or file path")
    parser.add_argument("--old", help="Old text for edit")
    parser.add_argument("--new", help="New text for edit")

    args = parser.parse_args()
    if args.tool != "summary" and not args.task:
        parser.error("task is required for this command")
    bridge = GeminiBridge()

    if args.tool == "browser":
        print(json.dumps(bridge.run_browser(args.task), indent=2))
    elif args.tool == "windows":
        print(json.dumps(bridge.run_windows(args.task), indent=2))
    elif args.tool == "worker":
        print(json.dumps(bridge.run_worker(args.task), indent=2))
    elif args.tool == "auto":
        print(json.dumps(bridge.run_auto(args.task), indent=2))
    elif args.tool == "edit":
        if not args.old or not args.new:
            print("Error: --old and --new required for edit")
        else:
            print(json.dumps(bridge.surgical_edit(args.task, args.old, args.new), indent=2))
    elif args.tool == "summary":
        print(json.dumps(bridge.summary(), indent=2))
