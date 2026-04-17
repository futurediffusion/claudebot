"""
Central model registry with available models and task routing metadata.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ModelType(Enum):
    PLANNING = "minimax-m2.7:cloud"
    HEAVY_CODING = "qwen3-coder:480b-cloud"
    FAST_CODING = "qwen3-coder-next:cloud"
    VISION = "qwen3-vl:latest"
    LIGHTWEIGHT = "gemma4:latest"
    GROQ_FAST = "groq_qwen_32b"
    GROQ_ULTRA_CHEAP = "groq_gpt_oss_20b"
    GROQ_VISION_SCOUT = "groq_vision_scout"


class TaskType(Enum):
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    HEAVY_REFACTOR = "heavy_refactor"
    MULTI_FILE_FIX = "multi_file_fix"
    FAST_CODING = "fast_coding"
    SCAFFOLDING = "scaffolding"
    VISION = "vision"
    SCREENSHOT = "screenshot"
    UI_ANALYSIS = "ui_analysis"
    SIMPLE_CLASSIFY = "simple_classify"
    SUMMARY = "summary"
    SIMPLE_EXEC = "simple_exec"
    LOG_ANALYSIS = "log_analysis"
    PARSING = "parsing"
    VALIDATION = "validation"
    FORMATTING = "formatting"
    CLASSIFICATION = "classification"
    JSON_GEN = "json"


@dataclass
class ModelConfig:
    name: str
    provider: str
    role: str
    strengths: List[str]
    weaknesses: List[str]
    cost_level: str
    cloud: bool
    timeout_seconds: int = 120


MODELS: dict[ModelType, ModelConfig] = {
    ModelType.PLANNING: ModelConfig(
        name="minimax-m2.7:cloud",
        provider="ollama",
        role="Planner / Strategist",
        strengths=[
            "Strategic planning",
            "Ambiguity resolution",
            "Architecture design",
            "Multi-step reasoning",
            "Decision making under uncertainty",
        ],
        weaknesses=[
            "Slow for simple tasks",
            "High cost per token",
        ],
        cost_level="high",
        cloud=True,
        timeout_seconds=180,
    ),
    ModelType.HEAVY_CODING: ModelConfig(
        name="qwen3-coder:480b-cloud",
        provider="ollama",
        role="Heavy Code Specialist",
        strengths=[
            "Multi-file refactoring",
            "Complex bug fixes",
            "Deep codebase analysis",
            "Code generation at scale",
            "Full feature implementation",
        ],
        weaknesses=[
            "Slow response time",
            "Expensive for simple edits",
        ],
        cost_level="high",
        cloud=True,
        timeout_seconds=300,
    ),
    ModelType.FAST_CODING: ModelConfig(
        name="qwen3-coder-next:cloud",
        provider="ollama",
        role="Fast Coding / Agentic",
        strengths=[
            "Quick scaffolding",
            "Single file edits",
            "Rapid prototyping",
            "Agentic task completion",
            "Fast iterations",
        ],
        weaknesses=[
            "Less suited for architecture",
            "May miss edge cases",
        ],
        cost_level="medium",
        cloud=True,
        timeout_seconds=120,
    ),
    ModelType.VISION: ModelConfig(
        name="qwen3-vl:latest",
        provider="ollama",
        role="Vision / UI Analysis",
        strengths=[
            "Screenshot analysis",
            "UI inspection",
            "Visual bug detection",
            "Image understanding",
        ],
        weaknesses=[
            "No code generation",
            "Not for planning",
            "Local model - limited context",
        ],
        cost_level="low",
        cloud=False,
        timeout_seconds=60,
    ),
    ModelType.LIGHTWEIGHT: ModelConfig(
        name="gemma4:latest",
        provider="ollama",
        role="Lightweight Helper",
        strengths=[
            "Simple classifications",
            "Quick summaries",
            "Cheap execution",
            "Fast responses",
        ],
        weaknesses=[
            "Limited reasoning",
            "Not for complex tasks",
        ],
        cost_level="low",
        cloud=False,
        timeout_seconds=30,
    ),
    ModelType.GROQ_FAST: ModelConfig(
        name="groq_qwen_32b",
        provider="groq",
        role="fast_brain",
        strengths=[
            "fast",
            "cheap",
            "parsing",
            "validation",
        ],
        weaknesses=[
            "not_for_architecture",
            "not_for_complex_reasoning",
            "not_for_deep_debugging",
        ],
        cost_level="low",
        cloud=True,
        timeout_seconds=15,
    ),
    ModelType.GROQ_ULTRA_CHEAP: ModelConfig(
        name="groq_gpt_oss_20b",
        provider="groq",
        role="ultra_cheap_worker",
        strengths=[
            "very_fast",
            "formatting",
            "json",
            "classification",
        ],
        weaknesses=[
            "very_limited_reasoning",
            "not_for_reasoning",
            "not_for_planning",
        ],
        cost_level="very_low",
        cloud=True,
        timeout_seconds=10,
    ),
    ModelType.GROQ_VISION_SCOUT: ModelConfig(
        name="llama-3.2-90b-vision-preview",
        provider="groq",
        role="Fast Vision Scout",
        strengths=[
            "Instant UI analysis",
            "Coordinate detection",
            "Success verification",
            "Zero cost (free tier)",
        ],
        weaknesses=[
            "Lower resolution than Gemini",
            "May hallucinate complex UI text",
        ],
        cost_level="zero",
        cloud=True,
        timeout_seconds=20,
    ),
}


def get_model_by_task(task_type: TaskType) -> ModelType:
    """Map a task type to the preferred model."""
    mapping = {
        TaskType.PLANNING: ModelType.PLANNING,
        TaskType.ARCHITECTURE: ModelType.PLANNING,
        TaskType.HEAVY_REFACTOR: ModelType.HEAVY_CODING,
        TaskType.MULTI_FILE_FIX: ModelType.HEAVY_CODING,
        TaskType.FAST_CODING: ModelType.FAST_CODING,
        TaskType.SCAFFOLDING: ModelType.FAST_CODING,
        TaskType.VISION: ModelType.GROQ_VISION_SCOUT,
        TaskType.SCREENSHOT: ModelType.GROQ_VISION_SCOUT,
        TaskType.UI_ANALYSIS: ModelType.GROQ_VISION_SCOUT,
        TaskType.SIMPLE_CLASSIFY: ModelType.LIGHTWEIGHT,
        TaskType.SUMMARY: ModelType.LIGHTWEIGHT,
        TaskType.SIMPLE_EXEC: ModelType.LIGHTWEIGHT,
        TaskType.LOG_ANALYSIS: ModelType.GROQ_FAST,
        TaskType.PARSING: ModelType.GROQ_FAST,
        TaskType.VALIDATION: ModelType.GROQ_FAST,
        TaskType.FORMATTING: ModelType.GROQ_ULTRA_CHEAP,
        TaskType.CLASSIFICATION: ModelType.GROQ_ULTRA_CHEAP,
        TaskType.JSON_GEN: ModelType.GROQ_ULTRA_CHEAP,
    }
    return mapping.get(task_type, ModelType.FAST_CODING)


def get_fallback_model(model_type: ModelType) -> Optional[ModelType]:
    """Get fallback model if a primary model is unavailable."""
    fallbacks = {
        ModelType.PLANNING: ModelType.FAST_CODING,
        ModelType.HEAVY_CODING: ModelType.FAST_CODING,
        ModelType.FAST_CODING: ModelType.LIGHTWEIGHT,
        ModelType.VISION: None,
        ModelType.GROQ_VISION_SCOUT: ModelType.VISION,
        ModelType.LIGHTWEIGHT: None,
        ModelType.GROQ_FAST: ModelType.LIGHTWEIGHT,
        ModelType.GROQ_ULTRA_CHEAP: ModelType.LIGHTWEIGHT,
    }
    return fallbacks.get(model_type)


def can_use_groq(task_type: TaskType) -> bool:
    """Return True when the task is a safe Groq fast-path."""
    groq_safe = {
        TaskType.LOG_ANALYSIS,
        TaskType.PARSING,
        TaskType.VALIDATION,
        TaskType.FORMATTING,
        TaskType.CLASSIFICATION,
        TaskType.JSON_GEN,
        TaskType.VISION,
        TaskType.SCREENSHOT,
        TaskType.UI_ANALYSIS,
    }
    return task_type in groq_safe


def should_not_use_groq(task_type: TaskType) -> bool:
    """Return True for tasks that should never go to Groq."""
    groq_forbidden = {
        TaskType.PLANNING,
        TaskType.ARCHITECTURE,
        TaskType.HEAVY_REFACTOR,
        TaskType.MULTI_FILE_FIX,
        TaskType.FAST_CODING,
        TaskType.SCAFFOLDING,
        TaskType.SIMPLE_EXEC,
    }
    return task_type in groq_forbidden


def classify_task(task_description: str) -> TaskType:
    """Classify a task description into TaskType."""
    task_lower = task_description.lower()
    fast_keywords = ["add ", "implement ", "create ", "write ", "fix ", "modify "]
    scaffold_keywords = ["scaffold", "boilerplate", "setup", "init", "new file"]
    validation_keywords = ["validate", "validation", "verify", "schema check", "consistency check"]
    json_keywords = ["format as json", "convert to json", "return json", "json object", "json schema"]
    classification_keywords = ["classify", "categorize", "label this", "tag this"]
    parsing_keywords = ["parse", "extract", "pull fields", "tokenize", "parse as"]
    formatting_keywords = ["format ", "reformat", "pretty print", "normalize formatting"]

    vision_keywords = ["screenshot", "image", "visual", "ui ", "interface", "screen"]
    if any(keyword in task_lower for keyword in vision_keywords) and "code" not in task_lower:
        if "screenshot" in task_lower or "screen" in task_lower:
            return TaskType.SCREENSHOT
        if "ui " in task_lower or "interface" in task_lower:
            return TaskType.UI_ANALYSIS
        return TaskType.VISION

    planning_keywords = ["plan", "strategy", "design", "architecture", "approach", "how should"]
    if any(keyword in task_lower for keyword in planning_keywords):
        return TaskType.PLANNING

    heavy_keywords = ["refactor", "multi-file", "rearchitect", "redesign", "complex bug", "entire"]
    if any(keyword in task_lower for keyword in heavy_keywords):
        return TaskType.HEAVY_REFACTOR

    if "fix" in task_lower and any(keyword in task_lower for keyword in ["file", "across", "multiple"]):
        return TaskType.MULTI_FILE_FIX

    coding_requested = any(keyword in task_lower for keyword in fast_keywords + scaffold_keywords)
    groq_processing_requested = any(keyword in task_lower for keyword in (
        validation_keywords + json_keywords + classification_keywords + parsing_keywords + formatting_keywords
    ))

    if coding_requested and groq_processing_requested:
        if any(keyword in task_lower for keyword in scaffold_keywords):
            return TaskType.SCAFFOLDING
        return TaskType.FAST_CODING

    log_keywords = ["log", "stack trace", "traceback", "error output"]
    if any(keyword in task_lower for keyword in log_keywords):
        return TaskType.LOG_ANALYSIS

    if any(keyword in task_lower for keyword in validation_keywords):
        return TaskType.VALIDATION

    if any(keyword in task_lower for keyword in json_keywords):
        return TaskType.JSON_GEN

    if any(keyword in task_lower for keyword in classification_keywords):
        return TaskType.CLASSIFICATION

    if any(keyword in task_lower for keyword in parsing_keywords):
        return TaskType.PARSING

    if any(keyword in task_lower for keyword in formatting_keywords):
        return TaskType.FORMATTING

    if any(keyword in task_lower for keyword in scaffold_keywords):
        return TaskType.SCAFFOLDING

    if any(keyword in task_lower for keyword in fast_keywords):
        return TaskType.FAST_CODING

    simple_keywords = ["summarize", "what is", "list ", "count ", "describe "]
    if any(keyword in task_lower for keyword in simple_keywords):
        return TaskType.SIMPLE_CLASSIFY

    return TaskType.FAST_CODING
