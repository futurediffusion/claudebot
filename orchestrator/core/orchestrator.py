"""
Orchestrator - coordinates routing, model execution, and tool usage.
"""

import json
import time
from typing import Any, Dict, Optional

from core.automation_detection import detect_automation_route
from core.context_manager import ContextManager
from core.router import Router
from core.task_logger import TaskLogger
from models.gemma4_adapter import Gemma4Adapter
from models.groq_adapter import GroqGPTAdapter, GroqQwenAdapter
from models.minimax_adapter import MinimaxAdapter
from models.model_registry import MODELS, ModelType, TaskType
from models.qwen480b_adapter import Qwen480bAdapter
from models.qwen_next_adapter import QwenNextAdapter
from models.qwen_vl_adapter import QwenVLAdapter
from tools.file_ops import FileOpsTool
from tools.run_shell import RunShellTool
from tools.screenshot import ScreenshotTool
from tools.worker_core_bridge import (
    BrowserAutomationTool,
    WindowsAutomationTool,
    WorkerOrchestratorTool,
)


class Orchestrator:
    """
    Main orchestrator for multi-model task execution.

    Flow:
    1. Receive task
    2. Route to model
    3. Execute with adapter
    4. Optionally run a Groq follow-up for lightweight validation
    5. Run tools if needed
    6. Log execution
    """

    def __init__(self):
        self.router = Router()
        self.logger = TaskLogger()
        self.context = ContextManager()

        self.adapters = {
            ModelType.PLANNING: MinimaxAdapter(),
            ModelType.HEAVY_CODING: Qwen480bAdapter(),
            ModelType.FAST_CODING: QwenNextAdapter(),
            ModelType.VISION: QwenVLAdapter(),
            ModelType.LIGHTWEIGHT: Gemma4Adapter(),
            ModelType.GROQ_FAST: GroqQwenAdapter(),
            ModelType.GROQ_ULTRA_CHEAP: GroqGPTAdapter(),
        }

        self.shell = RunShellTool()
        self.file_ops = FileOpsTool()
        self.screenshot = ScreenshotTool()
        self.browser_automation = BrowserAutomationTool()
        self.windows_automation = WindowsAutomationTool()
        self.worker_automation = WorkerOrchestratorTool()

    def execute(
        self,
        task: str,
        use_tools: bool = True,
        max_fallbacks: int = 1
    ) -> Dict[str, Any]:
        """
        Execute a task through the orchestrator.

        Args:
            task: The task description
            use_tools: Whether to enable tool execution
            max_fallbacks: Maximum fallback attempts after a failed execution

        Returns:
            Execution result dict
        """
        start_time = time.time()

        if use_tools:
            automation_route = detect_automation_route(task)
            if automation_route:
                return self._execute_automation_route(task, automation_route, start_time)

        model_type, task_type, reasoning, used_fallback = self.router.route_with_fallback(task, max_fallbacks)

        result = self._execute_with_model(
            task=task,
            model_type=model_type,
            task_type=task_type,
            reasoning=reasoning,
            used_fallback=used_fallback,
            use_tools=use_tools,
            start_time=start_time,
        )

        if result.get("success") or max_fallbacks <= 0:
            return result

        fallback_model = self.router.get_fallback(model_type)
        if fallback_model is None:
            return result

        fallback_reasoning = (
            f"{reasoning} Runtime fallback to '{MODELS[fallback_model].name}' "
            f"after error: {result.get('error', 'unknown error')}"
        )

        return self._execute_with_model(
            task=task,
            model_type=fallback_model,
            task_type=task_type,
            reasoning=fallback_reasoning,
            used_fallback=True,
            use_tools=use_tools,
            start_time=start_time,
        )

    def execute_with_model(
        self,
        task: str,
        model_name: str,
        forced_task_type: Optional[TaskType] = None,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task with a specific model and bypass routing.

        Args:
            task: The task description
            model_name: ModelType.value (for example "minimax-m2.7:cloud")
            forced_task_type: Optional task type when the caller already knows the phase
            use_tools: Whether to enable tool execution

        Returns:
            Execution result dict
        """
        start_time = time.time()

        model_type = None
        for candidate in ModelType:
            if candidate.value == model_name:
                model_type = candidate
                break

        if model_type is None:
            return {
                "success": False,
                "error": f"Unknown model: {model_name}",
                "model": model_name,
            }

        task_type = forced_task_type or self.router.classify(task)
        reasoning = f"Forced model selection: {model_name}"

        return self._execute_with_model(
            task=task,
            model_type=model_type,
            task_type=task_type,
            reasoning=reasoning,
            used_fallback=False,
            use_tools=use_tools,
            start_time=start_time,
        )

    def _execute_with_model(
        self,
        task: str,
        model_type: ModelType,
        task_type: TaskType,
        reasoning: str,
        used_fallback: bool,
        use_tools: bool,
        start_time: float
    ) -> Dict[str, Any]:
        """Internal method to execute with a specific model."""
        adapter = self.adapters[model_type]
        context = self.context.get_context()
        response = adapter.generate_response(task, context)

        follow_up = None
        tools_used = []
        tool_results: Dict[str, Any] = {}

        if response.get("success"):
            follow_up = self._maybe_run_lightweight_follow_up(
                task=task,
                task_type=task_type,
                model_type=model_type,
                primary_response=response.get("response", ""),
            )

            if use_tools and self._response_requests_tool(response.get("response", "")):
                tool_results = self._execute_tools(response["response"], task_type)
                tools_used = list(tool_results.keys())

        execution_time_ms = int((time.time() - start_time) * 1000)

        log_id = self.logger.log(
            task=task,
            model_type=model_type.value,
            task_type=task_type.value,
            tools_used=tools_used,
            result=response.get("response", "")[:500],
            error=response.get("error"),
            execution_time_ms=execution_time_ms,
            metadata={
                "reasoning": reasoning,
                "used_fallback": used_fallback,
                "follow_up_model": follow_up.get("model") if follow_up else None,
                "follow_up_task_type": follow_up.get("task_type") if follow_up else None,
            },
        )

        pipeline = [
            {
                "model": model_type.value,
                "task_type": task_type.value,
                "success": response.get("success", False),
            }
        ]
        if follow_up:
            pipeline.append({
                "model": follow_up["model"],
                "task_type": follow_up["task_type"],
                "success": follow_up["success"],
            })

        return {
            "log_id": log_id,
            "model": model_type.value,
            "model_role": adapter.__class__.__name__.replace("Adapter", ""),
            "task_type": task_type.value,
            "reasoning": reasoning,
            "response": response.get("response"),
            "error": response.get("error"),
            "tools_used": tools_used,
            "tool_results": tool_results,
            "execution_time_ms": execution_time_ms,
            "success": response.get("success", False),
            "follow_up": follow_up,
            "pipeline": pipeline,
        }

    def _execute_automation_route(
        self,
        task: str,
        route: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Run direct browser/windows/worker automation from natural language."""
        route_map = {
            "browser": {
                "executor": self.execute_browser_task,
                "model": "worker-core:browser",
                "task_type": "browser_automation",
                "model_role": "BrowserAutomation",
                "tool_name": "browser",
            },
            "windows": {
                "executor": self.execute_windows_task,
                "model": "worker-core:windows",
                "task_type": "windows_automation",
                "model_role": "WindowsAutomation",
                "tool_name": "windows",
            },
            "worker": {
                "executor": self.execute_worker_task,
                "model": "worker-core:orchestrator",
                "task_type": "worker_automation",
                "model_role": "WorkerAutomation",
                "tool_name": "worker",
            },
        }

        config = route_map[route]
        automation_result = config["executor"](task)
        execution_time_ms = int((time.time() - start_time) * 1000)
        success = automation_result.get("success", False)
        response_text = self._coerce_result_text(
            automation_result.get("content")
            or automation_result.get("response")
            or automation_result.get("stdout")
            or ("Automation completed successfully." if success else automation_result.get("error"))
        )
        reasoning = (
            f"Natural-language automation route detected. "
            f"Delegated directly to {config['model']} without LLM model selection."
        )

        log_id = self.logger.log(
            task=task,
            model_type=config["model"],
            task_type=config["task_type"],
            tools_used=[config["tool_name"]],
            result=response_text[:500],
            error=automation_result.get("error"),
            execution_time_ms=execution_time_ms,
            metadata={
                "reasoning": reasoning,
                "used_fallback": False,
                "automation_route": route,
            },
        )

        return {
            "log_id": log_id,
            "model": config["model"],
            "model_role": config["model_role"],
            "task_type": config["task_type"],
            "reasoning": reasoning,
            "response": response_text,
            "error": automation_result.get("error"),
            "tools_used": [config["tool_name"]],
            "tool_results": {config["tool_name"]: automation_result},
            "execution_time_ms": execution_time_ms,
            "success": success,
            "follow_up": None,
            "pipeline": [
                {
                    "model": config["model"],
                    "task_type": config["task_type"],
                    "success": success,
                }
            ],
            "automation_route": route,
        }

    def _maybe_run_lightweight_follow_up(
        self,
        task: str,
        task_type: TaskType,
        model_type: ModelType,
        primary_response: str
    ) -> Optional[Dict[str, Any]]:
        """
        Allow chaining a heavy or coding model into Groq validation.

        Example:
            qwen3-coder -> groq validation
        """
        if model_type in {ModelType.GROQ_FAST, ModelType.GROQ_ULTRA_CHEAP}:
            return None

        if task_type not in {
            TaskType.HEAVY_REFACTOR,
            TaskType.MULTI_FILE_FIX,
            TaskType.FAST_CODING,
            TaskType.SCAFFOLDING,
        }:
            return None

        follow_up_type = self._get_follow_up_task_type(task)
        if follow_up_type is None:
            return None

        follow_up_model = self.router.get_model(follow_up_type)
        if follow_up_model not in {ModelType.GROQ_FAST, ModelType.GROQ_ULTRA_CHEAP}:
            return None

        follow_up_task = self._build_follow_up_prompt(task, primary_response, follow_up_type)
        follow_up_response = self.adapters[follow_up_model].generate_response(follow_up_task)

        return {
            "model": follow_up_model.value,
            "task_type": follow_up_type.value,
            "success": follow_up_response.get("success", False),
            "response": follow_up_response.get("response"),
            "error": follow_up_response.get("error"),
        }

    def _get_follow_up_task_type(self, task: str) -> Optional[TaskType]:
        """Detect whether the original task asked for a lightweight Groq post-step."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["validate", "validation", "verify", "schema"]):
            return TaskType.VALIDATION
        if any(keyword in task_lower for keyword in ["format as json", "convert to json", "return json"]):
            return TaskType.JSON_GEN
        if any(keyword in task_lower for keyword in ["format ", "reformat", "pretty print"]):
            return TaskType.FORMATTING
        if any(keyword in task_lower for keyword in ["classify", "categorize", "label this"]):
            return TaskType.CLASSIFICATION
        return None

    def _build_follow_up_prompt(
        self,
        original_task: str,
        primary_response: str,
        follow_up_type: TaskType
    ) -> str:
        """Build a compact follow-up prompt for the Groq processing step."""
        truncated_response = primary_response[:6000]
        action = {
            TaskType.VALIDATION: "Validate the result and flag obvious issues or missing requirements.",
            TaskType.JSON_GEN: "Convert the result into valid JSON with stable keys.",
            TaskType.FORMATTING: "Format the result cleanly and consistently.",
            TaskType.CLASSIFICATION: "Classify the result into the most useful labels.",
        }.get(follow_up_type, "Process the result.")

        return (
            f"{action}\n\n"
            "Keep the answer compact.\n\n"
            f"Original task:\n{original_task}\n\n"
            f"Primary output:\n{truncated_response}"
        )

    def _coerce_result_text(self, value: Any) -> str:
        """Normalize structured tool output into a compact string."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except TypeError:
            return str(value)

    def _response_requests_tool(self, response: str) -> bool:
        """Return True when the model output contains an executable tool directive."""
        normalized = response.lower()
        markers = ("tool:", "shell:", "read:", "write:", "browser:", "windows:", "worker:")
        return any(marker in normalized for marker in markers)

    def _execute_tools(
        self,
        model_response: str,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """Execute requested tools based on model response."""
        del task_type
        results: Dict[str, Any] = {}

        if "shell:" in model_response.lower():
            for line in model_response.split("\n"):
                stripped_line = line.strip()
                if stripped_line.startswith("shell:"):
                    cmd = stripped_line.replace("shell:", "", 1).strip()
                    results["shell"] = self.shell.execute(cmd)

        if "read:" in model_response.lower():
            for line in model_response.split("\n"):
                stripped_line = line.strip()
                if stripped_line.startswith("read:"):
                    path = stripped_line.replace("read:", "", 1).strip()
                    results["file"] = self.file_ops.read(path)

        if "write:" in model_response.lower():
            for line in model_response.split("\n"):
                stripped_line = line.strip()
                if stripped_line.startswith("write:"):
                    parts = stripped_line.replace("write:", "", 1).split("|")
                    if len(parts) >= 2:
                        path = parts[0].strip()
                        content = "|".join(parts[1:]).strip()
                        results["file"] = self.file_ops.write(path, content)

        if "browser:" in model_response.lower():
            for line in model_response.split("\n"):
                stripped_line = line.strip()
                if stripped_line.startswith("browser:"):
                    browser_task = stripped_line.replace("browser:", "", 1).strip()
                    results["browser"] = self.browser_automation.execute(browser_task)

        if "windows:" in model_response.lower():
            for line in model_response.split("\n"):
                stripped_line = line.strip()
                if stripped_line.startswith("windows:"):
                    windows_task = stripped_line.replace("windows:", "", 1).strip()
                    results["windows"] = self.windows_automation.execute(windows_task)

        if "worker:" in model_response.lower():
            for line in model_response.split("\n"):
                stripped_line = line.strip()
                if stripped_line.startswith("worker:"):
                    worker_task = stripped_line.replace("worker:", "", 1).strip()
                    results["worker"] = self.worker_automation.execute(worker_task)

        return results

    def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        results = {}
        for model_type, adapter in self.adapters.items():
            results[model_type.value] = adapter.health_check()
        results["worker_core_browser"] = self.browser_automation.bridge.is_available()
        results["worker_core_windows"] = self.windows_automation.bridge.is_available()
        results["worker_core_orchestrator"] = self.worker_automation.bridge.is_available()
        return results

    def execute_browser_task(self, task: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Run a direct browser automation task through worker-core."""
        return self.browser_automation.execute(task, config_path=config_path)

    def execute_windows_task(self, task: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Run a direct Windows automation task through worker-core."""
        return self.windows_automation.execute(task, config_path=config_path)

    def execute_worker_task(self, task: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Run a full worker-core orchestration task."""
        return self.worker_automation.execute(task, config_path=config_path)

    def set_task_context(self, key: str, value: Any):
        """Set context for upcoming tasks."""
        self.context.set_state(key, value)

    def add_file_to_context(self, path: str):
        """Read and add file contents to task context."""
        result = self.file_ops.read(path)
        if result["success"]:
            self.context.add_file_context(path, result["content"])
