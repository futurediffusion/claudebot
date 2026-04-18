"""
Task decomposer - splits complex tasks into executable subtasks.
"""

from typing import Any, Dict, List, Optional

from core.automation_detection import detect_automation_route
from models.model_registry import TaskType


class TaskDecomposer:
    """
    Breaks complex tasks into executable subtasks.

    Each subtask includes:
    - description
    - model
    - task_type
    - depends_on
    """

    PLANNING_KEYWORDS = [
        "design", "architecture", "plan", "strategy", "approach",
        "how should", "organize", "structure", "best practices",
    ]

    HEAVY_CODING_KEYWORDS = [
        "refactor", "rearchitect", "redesign", "multi-file",
        "entire", "all files", "migrate", "rewrite",
    ]

    FAST_CODING_KEYWORDS = [
        "create", "add", "implement", "write", "modify",
        "change", "update", "fix", "create file", "new file",
    ]

    SCAFFOLDING_KEYWORDS = [
        "scaffold", "boilerplate", "setup", "init", "initialize",
        "new project", "new module",
    ]

    SIMPLE_KEYWORDS = [
        "list", "count", "what is", "explain", "summarize",
        "describe",
    ]

    TEST_KEYWORDS = [
        "test", "spec", "unit test", "integration test", "assert",
    ]

    VALIDATION_KEYWORDS = [
        "validate", "validation", "verify", "schema", "json",
        "format", "classification", "classify", "categorize",
        "check",
    ]

    def decompose(self, task: str) -> List[Dict[str, Any]]:
        """
        Break a complex task into ordered subtasks.

        Returns:
            Ordered list of subtasks
        """
        automation_route = detect_automation_route(task)
        if automation_route:
            return [self._create_automation_subtask(task, automation_route)]

        if self._is_simple_task(task):
            return [self._create_subtask(task, "Simple task", None)]

        subtasks: List[Dict[str, Any]] = []
        has_validation_phase = False

        if self._needs_planning(task):
            planning_subtask = self._create_subtask(
                "Plan the approach for: " + task,
                "Planning phase",
                TaskType.PLANNING,
            )
            planning_subtask["outputs"] = ["architecture", "plan", "structure"]
            subtasks.append(planning_subtask)

        if self._needs_coding(task):
            coding_type = self._get_coding_type(task)
            task_type = TaskType.HEAVY_REFACTOR if coding_type == "heavy" else TaskType.FAST_CODING

            coding_subtask = self._create_subtask(
                f"Implement/code for: {task}",
                "Coding phase",
                task_type,
            )
            coding_subtask["depends_on"] = [subtasks[-1]["id"]] if subtasks else None
            coding_subtask["outputs"] = ["files_created", "code_written"]
            subtasks.append(coding_subtask)

        if self._needs_tests(task) and subtasks:
            test_subtask = self._create_subtask(
                f"Write tests for: {task}",
                "Testing phase",
                TaskType.FAST_CODING,
            )
            test_subtask["depends_on"] = [subtasks[-1]["id"]]
            test_subtask["outputs"] = ["tests_written"]
            subtasks.append(test_subtask)

        if self._needs_validation(task) and subtasks:
            validation_task_type = self._get_validation_task_type(task)
            validation_subtask = self._create_subtask(
                self._build_validation_description(task, validation_task_type),
                "Validation phase",
                validation_task_type,
            )
            validation_subtask["depends_on"] = [subtasks[-1]["id"]]
            validation_subtask["outputs"] = ["validation"]
            subtasks.append(validation_subtask)
            has_validation_phase = True

        if subtasks and not has_validation_phase:
            final_subtask = self._create_subtask(
                "Verify the work is complete and correct",
                "Final verification phase",
                TaskType.SIMPLE_CLASSIFY,
            )
            final_subtask["depends_on"] = [subtasks[-1]["id"]]
            final_subtask["outputs"] = ["verification"]
            subtasks.append(final_subtask)

        if not subtasks:
            return [self._create_subtask(task, "Task execution", None)]

        return subtasks

    def _is_simple_task(self, task: str) -> bool:
        """Return True for one-shot tasks that do not need decomposition."""
        task_lower = task.lower()

        if len(task.split()) < 10 and not any(separator in task_lower for separator in [" and ", " then ", ", then"]):
            if any(keyword in task_lower for keyword in self.SIMPLE_KEYWORDS):
                return True
            if task_lower.startswith(("create ", "write ", "add ", "fix ", "validate ", "format ")):
                return len(task) < 100

        return False

    def _needs_planning(self, task: str) -> bool:
        """Return True when the task needs an explicit planning phase."""
        task_lower = task.lower()
        has_planning = any(keyword in task_lower for keyword in self.PLANNING_KEYWORDS)
        has_multiple_phases = any(separator in task_lower for separator in [" and ", ", then", " then "])
        is_complex = len(task) > 50
        return has_planning or (has_multiple_phases and is_complex)

    def _needs_coding(self, task: str) -> bool:
        """Return True when the task includes code creation or edits."""
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in self.FAST_CODING_KEYWORDS + self.HEAVY_CODING_KEYWORDS)

    def _needs_tests(self, task: str) -> bool:
        """Return True when the task explicitly asks for tests."""
        task_lower = task.lower()
        has_test_keyword = any(keyword in task_lower for keyword in self.TEST_KEYWORDS)
        has_multiple_phases = any(separator in task_lower for separator in [" and ", ", then", " then "])
        return has_test_keyword or (has_multiple_phases and len(task) > 80 and "test" in task_lower)

    def _needs_validation(self, task: str) -> bool:
        """Return True when the task asks for validation/formatting/classification."""
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in self.VALIDATION_KEYWORDS)

    def _get_coding_type(self, task: str) -> str:
        """Return 'heavy' or 'fast' coding."""
        task_lower = task.lower()
        if any(keyword in task_lower for keyword in self.HEAVY_CODING_KEYWORDS):
            return "heavy"
        return "fast"

    def _get_validation_task_type(self, task: str) -> TaskType:
        """Pick the Groq task type for the validation phase."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["format as json", "convert to json", "return json"]):
            return TaskType.JSON_GEN
        if any(keyword in task_lower for keyword in ["format ", "reformat", "pretty print"]):
            return TaskType.FORMATTING
        if any(keyword in task_lower for keyword in ["classify", "categorize", "label this"]):
            return TaskType.CLASSIFICATION
        if "log" in task_lower:
            return TaskType.LOG_ANALYSIS
        if "parse" in task_lower or "extract" in task_lower:
            return TaskType.PARSING
        return TaskType.VALIDATION

    def _build_validation_description(self, task: str, task_type: TaskType) -> str:
        """Build a compact validation subtask description."""
        descriptions = {
            TaskType.VALIDATION: f"Validate the result for: {task}",
            TaskType.LOG_ANALYSIS: f"Analyze logs and validate the result for: {task}",
            TaskType.PARSING: f"Parse and validate the output for: {task}",
            TaskType.FORMATTING: f"Format the output cleanly for: {task}",
            TaskType.CLASSIFICATION: f"Classify the output for: {task}",
            TaskType.JSON_GEN: f"Convert the output to valid JSON for: {task}",
        }
        return descriptions.get(task_type, f"Validate the result for: {task}")

    def _create_automation_subtask(self, task: str, route: str) -> Dict[str, Any]:
        """Keep desktop/browser automation as one direct worker-core step."""
        phase_map = {
            "browser": "Browser automation",
            "windows": "Windows automation",
            "worker": "Worker automation",
        }

        subtask = self._create_subtask(task, phase_map.get(route, "Automation"), None)
        subtask["route"] = route
        subtask["outputs"] = ["automation_result"]
        return subtask

    def _create_subtask(
        self,
        description: str,
        phase: str,
        task_type: Optional[TaskType]
    ) -> Dict[str, Any]:
        """Create a subtask with a short unique id."""
        import uuid

        subtask_id = str(uuid.uuid4())[:8]
        return {
            "id": subtask_id,
            "description": description,
            "phase": phase,
            "task_type": task_type.value if task_type else "generic",
            "model": None,
            "depends_on": None,
            "outputs": [],
            "result": None,
            "completed": False,
        }


class SingleAgentOrchestrator:
    """Execute a task as a sequence of subtasks using one shared agent/model path."""

    def __init__(self, agent_name: str = "claude_code", routing_mode: str = "locked_agent"):
        self.agent_name = agent_name
        self.routing_mode = routing_mode
        self.decomposer = TaskDecomposer()
        from core.orchestrator import Orchestrator
        self.base_orchestrator = Orchestrator(agent_name=self.agent_name, routing_mode=self.routing_mode)

    def execute_complex_task(self, task: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Execute a complex task after decomposition.

        Returns:
            Execution report for all subtasks
        """
        if verbose:
            print(f"\n{'=' * 60}")
            print(f"COMPLEX TASK: {task}")
            print(f"{'=' * 60}")

        subtasks = self.decomposer.decompose(task)

        if verbose:
            print(f"\n[PLAN] Decomposed into {len(subtasks)} subtasks:")
            for index, subtask in enumerate(subtasks, 1):
                dependency = f" (depends on: {subtask['depends_on']})" if subtask["depends_on"] else ""
                print(f"  {index}. [{subtask['phase']}] {subtask['description'][:60]}...{dependency}")

        results = []
        for index, subtask in enumerate(subtasks, 1):
            if verbose:
                print(f"\n--- Subtask {index}/{len(subtasks)} ---")
                print(f"Phase: {subtask['phase']}")

            result = self.base_orchestrator.execute(subtask["description"])

            subtask["result"] = result
            subtask["completed"] = result.get("success", False)

            if verbose:
                print(f"Model: {result['model']}")
                print(f"Success: {result['success']}")
                print(f"Time: {result['execution_time_ms']}ms")

            results.append({
                "subtask_id": subtask["id"],
                "phase": subtask["phase"],
                "model": result["model"],
                "success": result["success"],
                "execution_time_ms": result["execution_time_ms"],
            })

        successful = sum(1 for result in results if result["success"])
        total_time = sum(result["execution_time_ms"] for result in results)

        if verbose:
            print(f"\n{'=' * 60}")
            print(f"SUMMARY: {successful}/{len(results)} subtasks successful")
            print(f"Total time: {total_time}ms")
            print(f"{'=' * 60}")

        return {
            "original_task": task,
            "execution_mode": "single_agent",
            "routing_mode": self.routing_mode,
            "agent_locked": self.routing_mode == "locked_agent",
            "model_locked": self.base_orchestrator.router.resolve_locked_model(self.agent_name).value,
            "subtasks": subtasks,
            "results": results,
            "successful": successful,
            "total_time_ms": total_time,
            "all_success": successful == len(results),
        }


class MultiModelOrchestrator(SingleAgentOrchestrator):
    """
    Temporary compatibility alias.

    Deprecated: use SingleAgentOrchestrator.
    """
