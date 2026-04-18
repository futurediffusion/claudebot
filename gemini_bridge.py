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
    from core.episodic_memory import EpisodicMemoryEngine
    from core.self_model_engine import SelfModelEngine
    from core.world_model import WorldModelEngine
    from orchestrator.tools.mouse_calibration import MouseAutomationTool
    from orchestrator.tools.worker_core_bridge import (
        BrowserAutomationTool,
        WindowsAutomationTool,
        WorkerOrchestratorTool,
    )
except ImportError:
    print("Error: Could not import worker-core tools. Make sure you are in the claudebot root.")
    sys.exit(1)


class GeminiBridge:
    def __init__(self, execution_policy: str = "gemini_primary"):
        allowed_policies = {"gemini_primary", "legacy"}
        if execution_policy not in allowed_policies:
            raise ValueError(
                f"Unsupported execution_policy '{execution_policy}'. "
                f"Expected one of: {', '.join(sorted(allowed_policies))}."
            )
        self.execution_policy = execution_policy
        self.browser = BrowserAutomationTool()
        self.windows = WindowsAutomationTool()
        self.worker = WorkerOrchestratorTool()
        self.mouse = MouseAutomationTool(agent_name="gemini_cli")
        self.self_model = SelfModelEngine(agent_name="gemini_cli")
        self.episodic_memory = EpisodicMemoryEngine(agent_name="gemini_cli")
        self.world_model = WorldModelEngine(agent_name="gemini_cli")
        self.log_dir = ROOT / "gemini_memory"
        self.log_dir.mkdir(exist_ok=True)

    def _manual_switch_error(self, message: str, tool_plan: dict[str, object] | None = None):
        """Return a structured error when the request needs manual provider switching."""
        payload = {
            "success": False,
            "error": message,
            "needs_manual_agent_switch": True,
            "execution_policy": self.execution_policy,
            "supported_tools": ["browser", "windows", "worker", "edit"],
        }
        if tool_plan is not None:
            payload["self_model"] = tool_plan
        return payload

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
            "mouse": ("shared:mouse_calibration", "mouse_automation"),
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
            metadata={
                "source": "gemini_bridge",
                "decision_policy": "single_agent_cli",
            },
        )

    def _record_episode(self, tool_name, task, result):
        """Update the shared episodic memory from Gemini executions."""
        model_map = {
            "browser": ("worker-core:browser", "browser_automation", "automation"),
            "windows": ("worker-core:windows", "windows_automation", "automation"),
            "worker": ("worker-core:orchestrator", "worker_automation", "automation"),
            "mouse": ("shared:mouse_calibration", "mouse_automation", "automation"),
            "surgical_edit": ("gemini:surgical_edit", "file_edit", "file_edit"),
        }
        model_name, task_type, episode_type = model_map[tool_name]
        steps = [
            {
                "stage": f"tool:{tool_name}",
                "status": "completed" if result.get("success") else "failed",
                "detail": str(
                    result.get("content")
                    or result.get("response")
                    or result.get("path")
                    or result.get("error")
                    or ""
                )[:220],
            }
        ]
        if tool_name == "surgical_edit":
            steps.insert(
                0,
                {
                    "stage": "edit",
                    "status": "completed" if result.get("success") else "failed",
                    "detail": f"Applied surgical edit to {task}",
                },
            )

        self.episodic_memory.record_episode(
            task=task,
            task_type=task_type,
            success=result.get("success", False),
            execution_time_ms=0,
            episode_type=episode_type,
            model_name=model_name,
            tools_used=[tool_name],
            steps=steps,
            response=result.get("content") or result.get("response") or result.get("path"),
            error=result.get("error"),
            tool_results={tool_name: result},
            metadata={
                "source": "gemini_bridge",
                "decision_policy": "single_agent_cli",
            },
        )

    def _record_world_model(self, tool_name, task, result):
        """Update the shared world model from Gemini executions."""
        model_map = {
            "browser": ("worker-core:browser", "browser_automation", "browser"),
            "windows": ("worker-core:windows", "windows_automation", "windows"),
            "worker": ("worker-core:orchestrator", "worker_automation", "worker"),
            "mouse": ("shared:mouse_calibration", "mouse_automation", "windows"),
            "surgical_edit": ("gemini:surgical_edit", "file_edit", None),
        }
        model_name, task_type, route = model_map[tool_name]
        self.world_model.record_execution(
            task=task,
            task_type=task_type,
            success=result.get("success", False),
            model_name=model_name,
            route=route,
            tools_used=[tool_name],
            response=result.get("content") or result.get("response") or result.get("path"),
            error=result.get("error"),
            tool_results={tool_name: result},
            playbook_path=result.get("playbook"),
            metadata={
                "source": "gemini_bridge",
                "decision_policy": "single_agent_cli",
            },
        )

    def run_browser(self, task: str):
        print(f"Gemini -> Browser: {task}")
        self.world_model.record_task_start(
            task=task,
            task_type="browser_automation",
            route="browser",
            model_name="worker-core:browser",
        )
        result = self.browser.execute(task)
        self.log_action("browser", task, result)
        self._record_self_model("browser", task, result)
        self._record_episode("browser", task, result)
        self._record_world_model("browser", task, result)
        return result

    def run_windows(self, task: str):
        print(f"Gemini -> Windows: {task}")
        self.world_model.record_task_start(
            task=task,
            task_type="windows_automation",
            route="windows",
            model_name="worker-core:windows",
        )
        result = self.windows.execute(task)
        self.log_action("windows", task, result)
        self._record_self_model("windows", task, result)
        self._record_episode("windows", task, result)
        self._record_world_model("windows", task, result)
        return result

    def run_worker(self, task: str):
        print(f"Gemini -> Worker Core: {task}")
        self.world_model.record_task_start(
            task=task,
            task_type="worker_automation",
            route="worker",
            model_name="worker-core:orchestrator",
        )
        result = self.worker.execute(task)
        self.log_action("worker", task, result)
        self._record_self_model("worker", task, result)
        self._record_episode("worker", task, result)
        self._record_world_model("worker", task, result)
        return result

    def run_mouse(self, request: str | dict[str, object]):
        payload = json.loads(request) if isinstance(request, str) else request
        label = str(payload.get("label") or f"Mouse {payload.get('action', 'move')}")
        print(f"Gemini -> Mouse: {label}")
        self.world_model.record_task_start(
            task=label,
            task_type="mouse_automation",
            route="windows",
            model_name="shared:mouse_calibration",
        )
        result = self.mouse.execute(payload)
        self.log_action("mouse", label, result)
        self._record_self_model("mouse", label, result)
        self._record_episode("mouse", label, result)
        self._record_world_model("mouse", label, result)
        return result

    def run_auto(self, task: str):
        """Use the self-model to choose the best Gemini entrypoint."""
        tool_plan = self.self_model.suggest_tool(task, available_tools=["browser", "windows", "worker", "surgical_edit"])
        selected_tool = tool_plan.get("selected_tool", "worker")
        supported_auto_tools = {"browser", "windows", "worker"}

        if selected_tool in supported_auto_tools:
            if selected_tool == "browser":
                return self.run_browser(task)
            if selected_tool == "windows":
                return self.run_windows(task)
            return self.run_worker(task)

        if selected_tool == "surgical_edit":
            return self._manual_switch_error(
                "Self-model selected edit flow, but auto mode requires explicit file arguments (--old/--new).",
                tool_plan=tool_plan,
            )

        if self.execution_policy == "legacy":
            return self.run_worker(task)

        return self._manual_switch_error(
            f"Unsupported tool route for Gemini policy: {selected_tool}",
            tool_plan=tool_plan,
        )

    def surgical_edit(self, file_path: str, old_text: str, new_text: str):
        """Gemini's signature tool: precise text replacement."""
        print(f"Gemini -> Surgical Edit: {file_path}")
        self.world_model.record_task_start(
            task=f"Edit {file_path}",
            task_type="file_edit",
            route=None,
            model_name="gemini:surgical_edit",
        )
        path = Path(file_path)
        if not path.exists():
            result = {"success": False, "error": f"File {file_path} not found"}
            self._record_world_model("surgical_edit", f"Edit {file_path}", result)
            return result

        content = path.read_text(encoding="utf-8")
        if old_text not in content:
            result = {"success": False, "error": "Original text not found in file"}
            self._record_world_model("surgical_edit", f"Edit {file_path}", result)
            return result

        new_content = content.replace(old_text, new_text, 1)
        path.write_text(new_content, encoding="utf-8")

        result = {"success": True, "path": str(path)}
        self.log_action("surgical_edit", f"Edit {file_path}", result)
        self._record_self_model("surgical_edit", f"Edit {file_path}", result)
        self._record_episode("surgical_edit", f"Edit {file_path}", result)
        self._record_world_model("surgical_edit", f"Edit {file_path}", result)
        return result

    def summary(self):
        """Return shared self-model, episodic, and world summaries as seen by Gemini."""
        return {
            "self_model": self.self_model.get_summary(),
            "episodic_memory": self.episodic_memory.get_summary(),
            "world_model": self.world_model.get_summary(),
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Bridge CLI")
    parser.add_argument("tool", choices=["browser", "windows", "worker", "mouse", "auto", "edit", "summary"])
    parser.add_argument("task", nargs="?", help="Task or file path")
    parser.add_argument("--old", help="Old text for edit")
    parser.add_argument("--new", help="New text for edit")
    parser.add_argument(
        "--policy",
        choices=["gemini_primary", "legacy"],
        default="gemini_primary",
        help="Execution policy for routing behavior.",
    )

    args = parser.parse_args()
    if args.tool != "summary" and not args.task:
        parser.error("task is required for this command")
    bridge = GeminiBridge(execution_policy=args.policy)

    if args.tool == "browser":
        print(json.dumps(bridge.run_browser(args.task), indent=2))
    elif args.tool == "windows":
        print(json.dumps(bridge.run_windows(args.task), indent=2))
    elif args.tool == "worker":
        print(json.dumps(bridge.run_worker(args.task), indent=2))
    elif args.tool == "mouse":
        print(json.dumps(bridge.run_mouse(args.task), indent=2))
    elif args.tool == "auto":
        print(json.dumps(bridge.run_auto(args.task), indent=2))
    elif args.tool == "edit":
        if not args.old or not args.new:
            print("Error: --old and --new required for edit")
        else:
            print(json.dumps(bridge.surgical_edit(args.task, args.old, args.new), indent=2))
    elif args.tool == "summary":
        print(json.dumps(bridge.summary(), indent=2))
