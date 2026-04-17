from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

_WORKER_ROOT = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_bool_or_auto(name: str, default: bool | Literal["auto"]) -> bool | Literal["auto"]:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized == "auto":
        return "auto"
    return normalized in {"1", "true", "yes", "on"}


@dataclass
class Config:
    anthropic_api_key: str
    gemini_api_key: str | None
    anthropic_base_url: str | None
    model_name: str
    orchestrator_model: str
    windows_model: str
    browser_model: str

    worker_root: Path
    playbooks_dir: Path
    logs_dir: Path
    tasks_dir: Path
    memory_file: Path

    max_retries: int
    max_steps_windows: int
    max_steps_browser: int

    action_allowlist: list[str]

    browser_headless: bool
    browser_cdp_url: str | None
    browser_cdp_bootstrap_url: str
    browser_use_vision: bool | Literal["auto"]
    browser_channel: str | None
    browser_executable_path: str | None
    browser_user_data_dir: str | None
    browser_profile_directory: str | None

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        env_file = config_path or (_WORKER_ROOT / ".env")
        load_dotenv(dotenv_path=env_file, override=False)

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY no esta definida. "
                "Copia .env.example a .env y rellena el valor."
            )

        base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip() or None
        model_name = os.environ.get("MODEL_NAME", "minimax-m2.7:cloud")
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip() or None

        allowlist_raw = os.environ.get("ACTION_ALLOWLIST", "files,data")
        allowlist = [a.strip() for a in allowlist_raw.split(",") if a.strip()]

        worker_root = _WORKER_ROOT
        playbooks_dir = Path(os.environ.get("PLAYBOOKS_DIR", str(worker_root / "playbooks")))
        logs_dir = Path(os.environ.get("LOGS_DIR", str(worker_root / "logs")))
        tasks_dir = Path(os.environ.get("TASKS_DIR", str(worker_root / "tasks")))
        memory_file = Path(os.environ.get("MEMORY_FILE", str(worker_root / "memory.json")))

        for directory in (playbooks_dir, logs_dir, tasks_dir):
            directory.mkdir(parents=True, exist_ok=True)

        return cls(
            anthropic_api_key=api_key,
            gemini_api_key=gemini_api_key,
            anthropic_base_url=base_url,
            model_name=model_name,
            orchestrator_model=os.environ.get("ORCHESTRATOR_MODEL", model_name),
            windows_model=os.environ.get("WINDOWS_MODEL", model_name),
            browser_model=os.environ.get("BROWSER_MODEL", model_name),
            worker_root=worker_root,
            playbooks_dir=playbooks_dir,
            logs_dir=logs_dir,
            tasks_dir=tasks_dir,
            memory_file=memory_file,
            max_retries=int(os.environ.get("MAX_RETRIES", "1")),
            max_steps_windows=int(os.environ.get("MAX_STEPS_WINDOWS", "25")),
            max_steps_browser=int(os.environ.get("MAX_STEPS_BROWSER", "100")),
            action_allowlist=allowlist,
            browser_headless=_env_bool("BROWSER_HEADLESS", False),
            browser_cdp_url=os.environ.get("BROWSER_CDP_URL", "").strip() or None,
            browser_cdp_bootstrap_url=(
                os.environ.get(
                    "BROWSER_CDP_BOOTSTRAP_URL",
                    "https://www.freepik.com/pikaso/ai-image-generator",
                ).strip()
                or "https://www.freepik.com/pikaso/ai-image-generator"
            ),
            browser_use_vision=_env_bool_or_auto("BROWSER_USE_VISION", "auto"),
            browser_channel=os.environ.get("BROWSER_CHANNEL", "msedge").strip() or None,
            browser_executable_path=os.environ.get("BROWSER_EXECUTABLE_PATH", "").strip() or None,
            browser_user_data_dir=os.environ.get("BROWSER_USER_DATA_DIR", "").strip() or None,
            browser_profile_directory=os.environ.get("BROWSER_PROFILE_DIRECTORY", "").strip() or None,
        )
