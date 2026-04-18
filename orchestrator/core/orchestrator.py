"""
Orchestrator - coordinates routing, model execution, and tool usage.
"""

import json
import os
import time
from typing import Any, Dict, Optional

from core.automation_detection import detect_automation_route
from core.context_manager import ContextManager
from core.episodic_memory import EpisodicMemoryEngine
from core.router import Router
from core.task_logger import TaskLogger
from core.world_model import WorldModelEngine
from models.gemma4_adapter import Gemma4Adapter
from models.groq_adapter import GroqGPTAdapter, GroqQwenAdapter, GroqVisionScoutAdapter
from models.minimax_adapter import MinimaxAdapter
from models.model_registry import AGENT_PROFILES, MODELS, ModelType, TaskType, get_model_by_agent
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


def _env_flag_enabled(name: str) -> bool:
    """Return True when an env flag is set to a truthy value."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


class Orchestrator:
    """
    Main single-agent CLI-first orchestrator.

    Flow:
    1. Receive task
    2. Route to model
    3. Execute with adapter
    4. Optionally run a Groq follow-up for lightweight validation
    5. Run tools if needed
    6. Log execution
    """

    def __init__(self, agent_name: str = "claude_code", routing_mode: str = "locked_agent"):
        self.enable_groq_experimental = _env_flag_enabled("ENABLE_GROQ_EXPERIMENTAL")
        self.enable_local_multimodel_experimental = _env_flag_enabled("ENABLE_LOCAL_MULTIMODEL_EXPERIMENTAL")
        allow_legacy_routing = routing_mode != "locked_agent"
        self.agent_name = agent_name
        self.agent_default_model = get_model_by_agent(agent_name)
        self.agent_profile = AGENT_PROFILES.get((agent_name or "").strip().lower())
        self.router = Router(
            agent_name=agent_name,
            routing_mode=routing_mode,
            allow_legacy_routing=allow_legacy_routing,
        )
        self.self_model = self.router.self_model
        self.episodic_memory = EpisodicMemoryEngine(agent_name=agent_name)
        self.world_model = WorldModelEngine(agent_name=agent_name)
        self.logger = TaskLogger()
        self.context = ContextManager()

        self.adapters = {
            ModelType.PLANNING: MinimaxAdapter(),
            ModelType.HEAVY_CODING: Qwen480bAdapter(),
            ModelType.FAST_CODING: QwenNextAdapter(),
            ModelType.VISION: QwenVLAdapter(),
            ModelType.LIGHTWEIGHT: Gemma4Adapter(),
        }
        if self.enable_groq_experimental:
            self.adapters.update(
                {
                    ModelType.GROQ_FAST: GroqQwenAdapter(),
                    ModelType.GROQ_ULTRA_CHEAP: GroqGPTAdapter(),
                    ModelType.GROQ_VISION_SCOUT: GroqVisionScoutAdapter(),
                }
            )

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
                world_brief = self.world_model.build_context_brief(
                    task,
                    task_type=f"{automation_route}_automation",
                    refresh=True,
                )
                self._set_world_model_context(world_brief)
                self.world_model.record_task_start(
                    task=task,
                    task_type=f"{automation_route}_automation",
                    route=automation_route,
                    model_name=f"worker-core:{'orchestrator' if automation_route == 'worker' else automation_route}",
                    refresh_desktop=False,
                )
                memory_brief = self.episodic_memory.build_context_brief(
                    task,
                    task_type=f"{automation_route}_automation",
                )
                return self._execute_automation_route(
                    task,
                    automation_route,
                    start_time,
                    memory_brief,
                    world_brief,
                )

        model_type, task_type, reasoning, used_fallback = self.router.route_with_fallback(task, max_fallbacks)
        decision_meta = self.router.get_last_decision_meta()
        world_brief = self.world_model.build_context_brief(task, task_type=task_type.value, refresh=True)
        memory_brief = self.episodic_memory.build_context_brief(task, task_type=task_type.value)
        self._set_self_model_context(task, task_type.value, model_type.value, decision_meta)
        self._set_episodic_memory_context(memory_brief)
        self._set_world_model_context(world_brief)
        self.world_model.record_task_start(
            task=task,
            task_type=task_type.value,
            route=None,
            model_name=model_type.value,
            refresh_desktop=False,
        )

        result = self._execute_with_model(
            task=task,
            model_type=model_type,
            task_type=task_type,
            reasoning=reasoning,
            used_fallback=used_fallback,
            use_tools=use_tools,
            start_time=start_time,
            decision_meta=decision_meta,
            memory_brief=memory_brief,
            world_brief=world_brief,
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
        self.world_model.record_task_start(
            task=task,
            task_type=task_type.value,
            route=None,
            model_name=fallback_model.value,
            refresh_desktop=False,
        )

        return self._execute_with_model(
            task=task,
            model_type=fallback_model,
            task_type=task_type,
            reasoning=fallback_reasoning,
            used_fallback=True,
            use_tools=use_tools,
            start_time=start_time,
            memory_brief=memory_brief,
            world_brief=world_brief,
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
        decision_meta = {
            "task": task,
            "task_type": task_type.value,
            "default_model": model_name,
            "selected_model": model_name,
            "decision_simulation": {
                "selected_model": model_name,
                "default_model": model_name,
                "critic_notes": ["Forced model selection bypassed routing simulation."],
                "ranked_options": [
                    {
                        "model": model_name,
                        "score": 0,
                        "reasons": ["Forced model selection."],
                    }
                ],
            },
        }
        world_brief = self.world_model.build_context_brief(task, task_type=task_type.value, refresh=True)
        memory_brief = self.episodic_memory.build_context_brief(task, task_type=task_type.value)
        self._set_self_model_context(task, task_type.value, model_name, decision_meta)
        self._set_episodic_memory_context(memory_brief)
        self._set_world_model_context(world_brief)
        self.world_model.record_task_start(
            task=task,
            task_type=task_type.value,
            route=None,
            model_name=model_name,
            refresh_desktop=False,
        )

        return self._execute_with_model(
            task=task,
            model_type=model_type,
            task_type=task_type,
            reasoning=reasoning,
            used_fallback=False,
            use_tools=use_tools,
            start_time=start_time,
            decision_meta=decision_meta,
            memory_brief=memory_brief,
            world_brief=world_brief,
        )

    def _execute_with_model(
        self,
        task: str,
        model_type: ModelType,
        task_type: TaskType,
        reasoning: str,
        used_fallback: bool,
        use_tools: bool,
        start_time: float,
        decision_meta: Optional[Dict[str, Any]] = None,
        memory_brief: Optional[Dict[str, Any]] = None,
        world_brief: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Internal method to execute with a specific model."""
        if model_type not in self.adapters:
            return {
                "success": False,
                "error": (
                    f"Adapter for model '{model_type.value}' is disabled. "
                    "Enable the corresponding experimental feature flag to use it."
                ),
                "model": model_type.value,
                "task_type": task_type.value,
                "reasoning": reasoning,
            }

        adapter = self.adapters[model_type]
        context = self.context.get_context()
        response = adapter.generate_response(task, context)
        decision_meta = decision_meta or self.router.get_last_decision_meta()

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
        episode_steps = self._build_model_episode_steps(
            task_type=task_type,
            model_type=model_type,
            used_fallback=used_fallback,
            response=response,
            follow_up=follow_up,
            tools_used=tools_used,
            tool_results=tool_results,
            memory_brief=memory_brief,
        )

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
                "self_model": self._compact_self_model_meta(decision_meta),
                "episodic_memory": self._compact_episodic_memory(memory_brief),
                "world_model": self._compact_world_model(world_brief),
                "agent_profile_default_model": self.agent_default_model.value if self.agent_default_model else None,
            },
        )

        self.self_model.record_execution(
            task=task,
            task_type=task_type.value,
            model_name=model_type.value,
            success=response.get("success", False),
            execution_time_ms=execution_time_ms,
            error=response.get("error"),
            tools_used=tools_used,
            metadata={
                "reasoning": reasoning,
                "used_fallback": used_fallback,
                "follow_up_model": follow_up.get("model") if follow_up else None,
                "follow_up_task_type": follow_up.get("task_type") if follow_up else None,
                "agent_profile_default_model": self.agent_default_model.value if self.agent_default_model else None,
            },
            decision_simulation=decision_meta.get("decision_simulation") if decision_meta else None,
        )

        episode = self.episodic_memory.record_episode(
            task=task,
            task_type=task_type.value,
            success=response.get("success", False),
            execution_time_ms=execution_time_ms,
            episode_type="model_execution",
            model_name=model_type.value,
            tools_used=tools_used,
            steps=episode_steps,
            response=response.get("response"),
            error=response.get("error"),
            tool_results=tool_results,
            log_id=log_id,
            metadata={
                "reasoning": reasoning,
                "used_fallback": used_fallback,
                "follow_up": follow_up,
                "decision": self._compact_self_model_meta(decision_meta),
                "memory_hits": (memory_brief or {}).get("match_count", 0),
            },
        )
        world_update = self.world_model.record_execution(
            task=task,
            task_type=task_type.value,
            success=response.get("success", False),
            model_name=model_type.value,
            route=self._infer_world_route(task, tools_used),
            tools_used=tools_used,
            response=response.get("response"),
            error=response.get("error"),
            tool_results=tool_results,
            playbook_path=self._extract_playbook_path(tool_results),
            metadata={
                "reasoning": reasoning,
                "used_fallback": used_fallback,
                "follow_up": follow_up,
                "world_context": self._compact_world_model(world_brief),
                "agent_profile_default_model": self.agent_default_model.value if self.agent_default_model else None,
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
            "self_model": self._compact_self_model_meta(decision_meta),
            "episodic_memory": self._compact_episodic_memory(memory_brief),
            "world_model": self._compact_world_model(world_brief),
            "world_update": world_update,
            "episode_id": episode.get("id"),
            "agent_profile": {
                "agent": self.agent_name,
                "default_model": self.agent_default_model.value if self.agent_default_model else None,
                "supports_vision": self.agent_profile.supports_vision if self.agent_profile else None,
                "supports_tool_calls": self.agent_profile.supports_tool_calls if self.agent_profile else None,
                "cost_tier": self.agent_profile.cost_tier if self.agent_profile else None,
            },
        }

    def _execute_automation_route(
        self,
        task: str,
        route: str,
        start_time: float,
        memory_brief: Optional[Dict[str, Any]] = None,
        world_brief: Optional[Dict[str, Any]] = None,
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
        tool_plan = self.self_model.suggest_tool(task, available_tools=["browser", "windows", "worker"])
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
        if tool_plan.get("selected_tool") and tool_plan.get("selected_tool") != config["tool_name"]:
            reasoning += f" Self-model tool critic suggested '{tool_plan['selected_tool']}' but direct route won."
        if memory_brief and memory_brief.get("match_count"):
            recent_fix = next(
                (
                    item.get("resolution")
                    for item in memory_brief.get("matches", [])
                    if item.get("resolution")
                ),
                None,
            )
            reasoning += f" Episodic memory found {memory_brief['match_count']} similar run(s)."
            if recent_fix:
                reasoning += f" Latest known fix: {recent_fix}"
        if world_brief:
            active_window = (world_brief.get("active_window") or {}).get("title")
            pending_count = len(world_brief.get("pending_objectives", []))
            if active_window:
                reasoning += f" Active window before execution: {active_window}."
            if pending_count:
                reasoning += f" World model sees {pending_count} pending objective(s)."

        episode_steps = self._build_automation_episode_steps(
            route=route,
            success=success,
            response_text=response_text,
            tool_name=config["tool_name"],
            memory_brief=memory_brief,
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
                "self_model": self._compact_self_model_meta({"decision_simulation": tool_plan}),
                "episodic_memory": self._compact_episodic_memory(memory_brief),
                "world_model": self._compact_world_model(world_brief),
            },
        )

        self.self_model.record_execution(
            task=task,
            task_type=config["task_type"],
            model_name=config["model"],
            success=success,
            execution_time_ms=execution_time_ms,
            error=automation_result.get("error"),
            tools_used=[config["tool_name"]],
            metadata={"reasoning": reasoning, "automation_route": route},
            decision_simulation=tool_plan,
        )

        episode = self.episodic_memory.record_episode(
            task=task,
            task_type=config["task_type"],
            success=success,
            execution_time_ms=execution_time_ms,
            episode_type="automation",
            model_name=config["model"],
            tools_used=[config["tool_name"]],
            steps=episode_steps,
            response=response_text,
            error=automation_result.get("error"),
            tool_results={config["tool_name"]: automation_result},
            log_id=log_id,
            metadata={
                "reasoning": reasoning,
                "automation_route": route,
                "memory_hits": (memory_brief or {}).get("match_count", 0),
            },
        )
        world_update = self.world_model.record_execution(
            task=task,
            task_type=config["task_type"],
            success=success,
            model_name=config["model"],
            route=route,
            tools_used=[config["tool_name"]],
            response=response_text,
            error=automation_result.get("error"),
            tool_results={config["tool_name"]: automation_result},
            playbook_path=automation_result.get("playbook"),
            metadata={
                "reasoning": reasoning,
                "automation_route": route,
                "world_context": self._compact_world_model(world_brief),
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
            "self_model": self._compact_self_model_meta({"decision_simulation": tool_plan}),
            "episodic_memory": self._compact_episodic_memory(memory_brief),
            "world_model": self._compact_world_model(world_brief),
            "world_update": world_update,
            "episode_id": episode.get("id"),
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
        if follow_up_model not in self.adapters:
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

    def _set_self_model_context(
        self,
        task: str,
        task_type: str,
        selected_model: str,
        decision_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inject the current self-model brief into the execution context."""
        decision_meta = decision_meta or self.router.get_last_decision_meta()
        self.context.set_state(
            "self_model",
            self.self_model.build_execution_brief(
                task=task,
                task_type=task_type,
                selected_model=selected_model,
                decision=decision_meta.get("decision_simulation") if decision_meta else None,
                ),
        )

    def _set_episodic_memory_context(self, memory_brief: Optional[Dict[str, Any]]) -> None:
        """Inject relevant past episodes into the execution context."""
        self.context.set_state("episodic_memory", memory_brief or {"matches": [], "match_count": 0})

    def _set_world_model_context(self, world_brief: Optional[Dict[str, Any]]) -> None:
        """Inject the current desktop world model brief into the execution context."""
        self.context.set_state(
            "world_model",
            world_brief or {
                "active_window": {},
                "open_apps": [],
                "tabs": [],
                "files": [],
                "downloads_in_progress": [],
                "pending_objectives": [],
            },
        )

    def _compact_self_model_meta(self, decision_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Keep only the high-signal self-model metadata in results and logs."""
        if not decision_meta:
            return {}

        decision = decision_meta.get("decision_simulation", decision_meta)
        return {
            "selected_model": decision.get("selected_model"),
            "default_model": decision.get("default_model"),
            "selected_tool": decision.get("selected_tool"),
            "critic_notes": decision.get("critic_notes", [])[:2],
            "ranked_options": decision.get("ranked_options", [])[:2],
            "ranked_tools": decision.get("ranked_tools", [])[:2],
        }

    def _compact_episodic_memory(self, memory_brief: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Keep only the high-signal episodic hints in results and logs."""
        if not memory_brief:
            return {}

        return {
            "match_count": memory_brief.get("match_count", 0),
            "matches": [
                {
                    "task": item.get("task"),
                    "success": item.get("success"),
                    "failure": item.get("failure"),
                    "resolution": item.get("resolution"),
                }
                for item in memory_brief.get("matches", [])[:2]
            ],
        }

    def _compact_world_model(self, world_brief: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Keep only the high-signal world-state metadata in results and logs."""
        if not world_brief:
            return {}

        return {
            "active_window": world_brief.get("active_window"),
            "open_apps": world_brief.get("open_apps", [])[:3],
            "tabs": world_brief.get("tabs", [])[:2],
            "files": world_brief.get("files", [])[:3],
            "downloads_in_progress": world_brief.get("downloads_in_progress", [])[:3],
            "pending_objectives": world_brief.get("pending_objectives", [])[:3],
        }

    def _infer_world_route(self, task: str, tools_used: list[str]) -> Optional[str]:
        """Infer which desktop/browser route affected the world state."""
        route = detect_automation_route(task)
        if route:
            return route
        for tool_name in tools_used:
            if tool_name in {"browser", "windows", "worker"}:
                return tool_name
        return None

    def _extract_playbook_path(self, tool_results: Dict[str, Any]) -> Optional[str]:
        """Find a worker-core playbook path inside nested tool results."""
        for result in tool_results.values():
            if isinstance(result, dict) and result.get("playbook"):
                return result["playbook"]
        return None

    def _build_model_episode_steps(
        self,
        task_type: TaskType,
        model_type: ModelType,
        used_fallback: bool,
        response: Dict[str, Any],
        follow_up: Optional[Dict[str, Any]],
        tools_used: list[str],
        tool_results: Dict[str, Any],
        memory_brief: Optional[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        steps = [
            {
                "stage": "route",
                "status": "completed",
                "detail": (
                    f"Classified as {task_type.value} and selected {model_type.value}."
                    + (" Runtime fallback path was active." if used_fallback else "")
                ),
            }
        ]
        if memory_brief and memory_brief.get("match_count"):
            steps.append(
                {
                    "stage": "episodic_recall",
                    "status": "completed",
                    "detail": f"Loaded {memory_brief['match_count']} similar episode(s) into context.",
                }
            )
        steps.append(
            {
                "stage": "model_execution",
                "status": "completed" if response.get("success") else "failed",
                "detail": self._coerce_result_text(response.get("response") or response.get("error"))[:220],
            }
        )

        for tool_name in tools_used:
            result = tool_results.get(tool_name, {})
            steps.append(
                {
                    "stage": f"tool:{tool_name}",
                    "status": "completed" if result.get("success", True) else "failed",
                    "detail": self._coerce_result_text(
                        result.get("content") or result.get("response") or result.get("error")
                    )[:220],
                }
            )

        if follow_up:
            steps.append(
                {
                    "stage": "follow_up",
                    "status": "completed" if follow_up.get("success") else "failed",
                    "detail": (
                        f"{follow_up.get('model')} handled {follow_up.get('task_type')}."
                    ),
                }
            )
        return steps

    def _build_automation_episode_steps(
        self,
        route: str,
        success: bool,
        response_text: str,
        tool_name: str,
        memory_brief: Optional[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        steps = [
            {
                "stage": "route",
                "status": "completed",
                "detail": f"Natural-language automation routed to {route}.",
            }
        ]
        if memory_brief and memory_brief.get("match_count"):
            steps.append(
                {
                    "stage": "episodic_recall",
                    "status": "completed",
                    "detail": f"Reviewed {memory_brief['match_count']} similar automation episode(s).",
                }
            )
        steps.append(
            {
                "stage": f"tool:{tool_name}",
                "status": "completed" if success else "failed",
                "detail": response_text[:220],
            }
        )
        return steps

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
