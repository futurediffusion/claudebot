"""
Shared calibrated mouse automation backend for Gemini, Claude, Codex, and root CLIs.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import json
import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from PIL import ImageChops, ImageGrab, ImageStat
except ImportError:  # pragma: no cover - optional runtime dependency
    ImageChops = None
    ImageGrab = None
    ImageStat = None

try:
    from core.episodic_memory import EpisodicMemoryEngine
    from core.self_model_engine import SelfModelEngine
    from core.world_model import WorldModelEngine
except ImportError:
    from ..core.episodic_memory import EpisodicMemoryEngine
    from ..core.self_model_engine import SelfModelEngine
    from ..core.world_model import WorldModelEngine


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_PATH = ROOT_DIR / "world_model" / "mouse_calibration.json"
DEFAULT_HISTORY_PATH = ROOT_DIR / "episodic_memory" / "mouse_calibration.jsonl"
MOUSE_MODEL_NAME = "shared:mouse_calibration"
MOUSE_TASK_TYPE = "mouse_automation"

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


DEFAULT_PROFILE: dict[str, Any] = {
    "version": 1,
    "updated_at": None,
    "global": {
        "offset_x": 0.0,
        "offset_y": 0.0,
        "runs": 0,
        "successes": 0,
        "failures": 0,
        "last_error": None,
    },
    "contexts": {},
}


@dataclass
class MouseActionRequest:
    x: float
    y: float
    action: str = "move"
    coordinate_space: str = "absolute"
    source_width: Optional[int] = None
    source_height: Optional[int] = None
    image_path: Optional[str] = None
    label: Optional[str] = None
    verification_mode: str = "cursor"
    expected_window_title: Optional[str] = None
    expected_process_name: Optional[str] = None
    expected_rgb: Optional[tuple[int, int, int]] = None
    color_tolerance: int = 24
    verify_region_px: int = 80
    screen_diff_threshold: float = 4.0
    tolerance_px: int = 2
    max_attempts: int = 5
    search_step_px: int = 8
    search_radius_px: int = 24
    move_duration_ms: int = 180
    move_steps: int = 12
    settle_ms: int = 120
    click_pause_ms: int = 90
    profile_key: Optional[str] = None
    dry_run: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MouseActionRequest":
        if "x" not in payload or "y" not in payload:
            raise ValueError("Mouse request requires 'x' and 'y'.")

        action = _normalize_action(str(payload.get("action") or payload.get("button") or "move"))
        coordinate_space = str(payload.get("coordinate_space") or payload.get("space") or "absolute").lower()
        verification_mode = str(
            payload.get("verification_mode")
            or payload.get("verify")
            or "cursor"
        ).lower()

        return cls(
            x=float(payload["x"]),
            y=float(payload["y"]),
            action=action,
            coordinate_space=coordinate_space,
            source_width=_coerce_int(payload.get("source_width")),
            source_height=_coerce_int(payload.get("source_height")),
            image_path=_coerce_str(payload.get("image_path")),
            label=_coerce_str(payload.get("label")),
            verification_mode=verification_mode,
            expected_window_title=_coerce_str(
                payload.get("expected_window_title") or payload.get("expect_window_title")
            ),
            expected_process_name=_coerce_str(
                payload.get("expected_process_name") or payload.get("expect_process")
            ),
            expected_rgb=_parse_rgb(payload.get("expected_rgb")),
            color_tolerance=_coerce_int(payload.get("color_tolerance"), 24),
            verify_region_px=_coerce_int(payload.get("verify_region_px"), 80),
            screen_diff_threshold=_coerce_float(payload.get("screen_diff_threshold"), 4.0),
            tolerance_px=_coerce_int(payload.get("tolerance_px"), 2),
            max_attempts=_coerce_int(payload.get("max_attempts"), 5),
            search_step_px=_coerce_int(payload.get("search_step_px"), 8),
            search_radius_px=_coerce_int(payload.get("search_radius_px"), 24),
            move_duration_ms=_coerce_int(payload.get("move_duration_ms"), 180),
            move_steps=_coerce_int(payload.get("move_steps"), 12),
            settle_ms=_coerce_int(payload.get("settle_ms"), 120),
            click_pause_ms=_coerce_int(payload.get("click_pause_ms"), 90),
            profile_key=_coerce_str(payload.get("profile_key")),
            dry_run=bool(payload.get("dry_run", False)),
            metadata=_coerce_metadata(payload.get("metadata")),
        )

    def task_description(self) -> str:
        base = f"Mouse {self.action} at ({self.x}, {self.y})"
        if self.label:
            base += f" for {self.label}"
        if self.coordinate_space != "absolute":
            base += f" [{self.coordinate_space}]"
        return base


class WindowsMouseBackend:
    """Native Windows mouse backend with smooth movement and screenshots."""

    def __init__(self) -> None:
        if not hasattr(ctypes, "windll"):
            raise OSError("Native mouse automation is only available on Windows.")
        self.user32 = ctypes.windll.user32

    def screen_size(self) -> tuple[int, int]:
        return int(self.user32.GetSystemMetrics(0)), int(self.user32.GetSystemMetrics(1))

    def get_position(self) -> tuple[int, int]:
        point = POINT()
        if not self.user32.GetCursorPos(ctypes.byref(point)):
            raise OSError("GetCursorPos failed.")
        return int(point.x), int(point.y)

    def move_to(self, x: int, y: int, duration_ms: int = 180, steps: int = 12) -> tuple[int, int]:
        start_x, start_y = self.get_position()
        steps = max(1, int(steps))
        duration_s = max(duration_ms, 0) / 1000

        if duration_s <= 0 or steps == 1:
            self.user32.SetCursorPos(int(x), int(y))
            return self.get_position()

        sleep_per_step = duration_s / steps
        for index in range(1, steps + 1):
            progress = index / steps
            eased = 1 - math.pow(1 - progress, 2)
            current_x = round(start_x + ((int(x) - start_x) * eased))
            current_y = round(start_y + ((int(y) - start_y) * eased))
            self.user32.SetCursorPos(current_x, current_y)
            time.sleep(sleep_per_step)
        return self.get_position()

    def click(self, action: str) -> None:
        normalized = _normalize_action(action)
        if normalized == "move":
            return
        if normalized == "click":
            self._button_click("left")
            return
        if normalized == "right_click":
            self._button_click("right")
            return
        if normalized == "double_click":
            self._button_click("left")
            time.sleep(0.05)
            self._button_click("left")
            return
        raise ValueError(f"Unsupported mouse action: {action}")

    def capture_region(self, bbox: tuple[int, int, int, int]):
        if ImageGrab is None:
            return None
        return ImageGrab.grab(bbox=bbox)

    def sample_pixel(self, x: int, y: int) -> Optional[tuple[int, int, int]]:
        if ImageGrab is None:
            return None
        image = ImageGrab.grab(bbox=(int(x), int(y), int(x) + 1, int(y) + 1))
        pixel = image.getpixel((0, 0))
        if isinstance(pixel, int):
            return (pixel, pixel, pixel)
        return tuple(int(channel) for channel in pixel[:3])

    def _button_click(self, button: str) -> None:
        if button == "left":
            self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            return
        if button == "right":
            self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            return
        raise ValueError(f"Unsupported button: {button}")


class MouseCalibrationStore:
    """Persist learned offsets and append execution history."""

    def __init__(self, profile_path: Path | str = DEFAULT_PROFILE_PATH, history_path: Path | str = DEFAULT_HISTORY_PATH):
        self.profile_path = Path(profile_path)
        self.history_path = Path(history_path)
        self._ensure_profile()

    def load_profile(self) -> dict[str, Any]:
        with open(self.profile_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def get_offsets(self, context_key: str) -> dict[str, Any]:
        profile = self.load_profile()
        global_profile = profile.get("global", {})
        context_profile = profile.get("contexts", {}).get(context_key, {})
        return {
            "global_offset": {
                "x": float(global_profile.get("offset_x", 0.0)),
                "y": float(global_profile.get("offset_y", 0.0)),
            },
            "context_offset": {
                "x": float(context_profile.get("offset_x", 0.0)),
                "y": float(context_profile.get("offset_y", 0.0)),
            },
        }

    def update_profile(
        self,
        context_key: str,
        context_snapshot: dict[str, Any],
        verification_mode: str,
        success: bool,
        learned_offset: Optional[tuple[int, int]],
        error: Optional[str],
    ) -> dict[str, Any]:
        profile = self.load_profile()
        profile["updated_at"] = _timestamp()

        global_profile = profile.setdefault("global", copy.deepcopy(DEFAULT_PROFILE["global"]))
        context_profile = profile.setdefault("contexts", {}).setdefault(
            context_key,
            {
                "offset_x": 0.0,
                "offset_y": 0.0,
                "runs": 0,
                "successes": 0,
                "failures": 0,
                "last_error": None,
                "last_verified_at": None,
                "verification_modes": {},
                "context_snapshot": context_snapshot,
            },
        )
        context_profile["context_snapshot"] = context_snapshot

        self._bump_stats(global_profile, success, error)
        self._bump_stats(context_profile, success, error)

        mode_stats = context_profile.setdefault("verification_modes", {}).setdefault(
            verification_mode,
            {"runs": 0, "successes": 0, "failures": 0},
        )
        self._bump_stats(mode_stats, success, error)

        if success and learned_offset is not None:
            context_profile["offset_x"] = _blend(context_profile.get("offset_x", 0.0), learned_offset[0], 0.35)
            context_profile["offset_y"] = _blend(context_profile.get("offset_y", 0.0), learned_offset[1], 0.35)
            global_profile["offset_x"] = _blend(global_profile.get("offset_x", 0.0), learned_offset[0], 0.12)
            global_profile["offset_y"] = _blend(global_profile.get("offset_y", 0.0), learned_offset[1], 0.12)
            context_profile["last_verified_at"] = _timestamp()

        self._write_json(self.profile_path, profile)
        return profile

    def record_history(self, payload: dict[str, Any]) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _ensure_profile(self) -> None:
        if self.profile_path.exists():
            current = self._read_json(self.profile_path)
            merged = _merge_dicts(copy.deepcopy(DEFAULT_PROFILE), current)
            if merged != current:
                self._write_json(self.profile_path, merged)
            return
        self._write_json(self.profile_path, copy.deepcopy(DEFAULT_PROFILE))

    def _read_json(self, path: Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temp_path.replace(path)

    def _bump_stats(self, stats: dict[str, Any], success: bool, error: Optional[str]) -> None:
        stats["runs"] = int(stats.get("runs", 0)) + 1
        if success:
            stats["successes"] = int(stats.get("successes", 0)) + 1
        else:
            stats["failures"] = int(stats.get("failures", 0)) + 1
            stats["last_error"] = error


class MouseAutomationTool:
    """Coordinate mapping, calibrated motion, verification, and shared learning."""

    def __init__(
        self,
        agent_name: str = "shared_cli",
        backend: Optional[Any] = None,
        profile_path: Path | str = DEFAULT_PROFILE_PATH,
        history_path: Path | str = DEFAULT_HISTORY_PATH,
        self_model: Optional[Any] = None,
        episodic_memory: Optional[Any] = None,
        world_model: Optional[Any] = None,
    ) -> None:
        self.agent_name = agent_name
        self.backend = backend or WindowsMouseBackend()
        self.store = MouseCalibrationStore(profile_path=profile_path, history_path=history_path)
        self.self_model = self_model or SelfModelEngine(agent_name=agent_name)
        self.episodic_memory = episodic_memory or EpisodicMemoryEngine(agent_name=agent_name)
        self.world_model = world_model or WorldModelEngine(agent_name=agent_name)

    def execute(self, request: MouseActionRequest | dict[str, Any]) -> dict[str, Any]:
        req = request if isinstance(request, MouseActionRequest) else MouseActionRequest.from_payload(request)
        task = req.task_description()
        screen_width, screen_height = self.backend.screen_size()
        active_window = self._active_window(refresh=True)
        context_key = req.profile_key or self._context_key(active_window, screen_width, screen_height)

        if hasattr(self.world_model, "record_task_start"):
            self.world_model.record_task_start(
                task=task,
                task_type=MOUSE_TASK_TYPE,
                route="windows",
                model_name=MOUSE_MODEL_NAME,
                refresh_desktop=False,
            )

        mapped_target = self._map_coordinates(req, screen_width, screen_height)
        offsets = self.store.get_offsets(context_key)
        base_target = self._clamp_point(
            round(mapped_target[0] + offsets["global_offset"]["x"] + offsets["context_offset"]["x"]),
            round(mapped_target[1] + offsets["global_offset"]["y"] + offsets["context_offset"]["y"]),
            screen_width,
            screen_height,
        )

        attempts: list[dict[str, Any]] = []
        successful_attempt = None
        error_text = None
        attempt_offsets = self._build_attempt_offsets(req.max_attempts, req.search_step_px, req.search_radius_px)

        for attempt_index, search_offset in enumerate(attempt_offsets, start=1):
            candidate = self._clamp_point(
                base_target[0] + search_offset[0],
                base_target[1] + search_offset[1],
                screen_width,
                screen_height,
            )

            if req.dry_run:
                attempt = {
                    "attempt": attempt_index,
                    "candidate": {"x": candidate[0], "y": candidate[1]},
                    "actual": {"x": candidate[0], "y": candidate[1]},
                    "search_offset": {"x": search_offset[0], "y": search_offset[1]},
                    "distance_px": 0.0,
                    "clicked": req.action != "move",
                    "verification": {
                        "mode": req.verification_mode,
                        "cursor_position_ok": True,
                        "verified": True,
                        "confidence": "simulated",
                    },
                    "success": True,
                    "reason": "dry_run",
                }
                attempts.append(attempt)
                successful_attempt = attempt
                break

            before_window = self._active_window(refresh=False)
            before_capture = self._capture_verification_region(candidate, req.verify_region_px)
            self.backend.move_to(
                candidate[0],
                candidate[1],
                duration_ms=req.move_duration_ms,
                steps=req.move_steps,
            )
            time.sleep(req.settle_ms / 1000)
            actual_position = self.backend.get_position()
            distance_px = _distance(candidate, actual_position)
            position_ok = distance_px <= req.tolerance_px

            clicked = False
            if position_ok and req.action != "move":
                self.backend.click(req.action)
                clicked = True
                time.sleep(req.click_pause_ms / 1000)

            verification = self._verify_attempt(
                req=req,
                candidate=candidate,
                actual=actual_position,
                before_capture=before_capture,
                before_window=before_window,
            )
            attempt_success = bool(verification.get("verified"))
            reason = None
            if not position_ok:
                reason = "cursor_position_mismatch"
            elif not attempt_success:
                reason = verification.get("reason") or "verification_failed"

            attempt = {
                "attempt": attempt_index,
                "candidate": {"x": candidate[0], "y": candidate[1]},
                "actual": {"x": actual_position[0], "y": actual_position[1]},
                "search_offset": {"x": search_offset[0], "y": search_offset[1]},
                "distance_px": round(distance_px, 2),
                "clicked": clicked,
                "verification": verification,
                "success": attempt_success,
                "reason": reason,
            }
            attempts.append(attempt)

            if attempt_success:
                successful_attempt = attempt
                break

        if successful_attempt:
            success = True
            final_attempt = successful_attempt
            learned_offset = (
                successful_attempt["search_offset"]["x"],
                successful_attempt["search_offset"]["y"],
            )
        else:
            success = False
            final_attempt = min(attempts, key=lambda item: item["distance_px"]) if attempts else None
            learned_offset = None
            error_text = self._build_failure_reason(attempts)

        if req.dry_run:
            profile = self.store.load_profile()
        else:
            profile = self.store.update_profile(
                context_key=context_key,
                context_snapshot={
                    "active_window": active_window,
                    "screen": {"width": screen_width, "height": screen_height},
                },
                verification_mode=req.verification_mode,
                success=success,
                learned_offset=learned_offset,
                error=error_text,
            )

        response_text = self._build_response_text(success, req, final_attempt, context_key)
        result = {
            "success": success,
            "task_type": MOUSE_TASK_TYPE,
            "task": task,
            "action": req.action,
            "label": req.label,
            "coordinate_space": req.coordinate_space,
            "requested": {
                "x": req.x,
                "y": req.y,
                "source_width": req.source_width,
                "source_height": req.source_height,
                "image_path": req.image_path,
            },
            "mapped_target": {"x": mapped_target[0], "y": mapped_target[1]},
            "calibrated_target": {"x": base_target[0], "y": base_target[1]},
            "final_target": final_attempt["candidate"] if final_attempt else None,
            "actual_position": final_attempt["actual"] if final_attempt else None,
            "verification": final_attempt["verification"] if final_attempt else {},
            "attempt_count": len(attempts),
            "attempts": attempts,
            "context": {
                "profile_key": context_key,
                "active_window": active_window,
                "screen": {"width": screen_width, "height": screen_height},
            },
            "calibration": {
                "global_offset": profile["global"],
                "context_offset": profile.get("contexts", {}).get(
                    context_key,
                    {
                        "offset_x": offsets["context_offset"]["x"],
                        "offset_y": offsets["context_offset"]["y"],
                    },
                ),
                "profile_path": str(self.store.profile_path),
                "history_path": str(self.store.history_path),
                "learned_offset": {
                    "x": learned_offset[0],
                    "y": learned_offset[1],
                } if learned_offset else None,
            },
            "response": response_text,
            "content": response_text,
            "error": error_text,
            "dry_run": req.dry_run,
        }

        if not req.dry_run:
            self.store.record_history(
                {
                    "timestamp": _timestamp(),
                    "agent": self.agent_name,
                    "task": task,
                    "success": success,
                    "profile_key": context_key,
                    "action": req.action,
                    "verification_mode": req.verification_mode,
                    "attempt_count": len(attempts),
                    "mapped_target": result["mapped_target"],
                    "final_target": result["final_target"],
                    "actual_position": result["actual_position"],
                    "error": error_text,
                }
            )

            self._record_shared_learning(req, result)
        return result

    def _record_shared_learning(self, req: MouseActionRequest, result: dict[str, Any]) -> None:
        task = result["task"]
        success = result["success"]
        error = result.get("error")
        response = result.get("response")
        attempts = result.get("attempts", [])

        steps = [
            {
                "stage": "mouse_mapping",
                "status": "completed",
                "detail": (
                    f"Mapped {req.coordinate_space} coordinates to "
                    f"{result['mapped_target']['x']},{result['mapped_target']['y']}."
                ),
            }
        ]
        for attempt in attempts:
            steps.append(
                {
                    "stage": f"mouse_attempt_{attempt['attempt']}",
                    "status": "completed" if attempt["success"] else "failed",
                    "detail": (
                        f"Candidate {attempt['candidate']['x']},{attempt['candidate']['y']} "
                        f"actual {attempt['actual']['x']},{attempt['actual']['y']} "
                        f"verified={attempt['verification'].get('verified')}"
                    ),
                }
            )

        if hasattr(self.self_model, "record_execution"):
            self.self_model.record_execution(
                task=task,
                task_type=MOUSE_TASK_TYPE,
                model_name=MOUSE_MODEL_NAME,
                success=success,
                execution_time_ms=0,
                error=error,
                tools_used=["mouse"],
                metadata={
                    "verification_mode": req.verification_mode,
                    "coordinate_space": req.coordinate_space,
                    "attempt_count": len(attempts),
                },
            )

        if hasattr(self.episodic_memory, "record_episode"):
            self.episodic_memory.record_episode(
                task=task,
                task_type=MOUSE_TASK_TYPE,
                success=success,
                execution_time_ms=0,
                episode_type="automation",
                model_name=MOUSE_MODEL_NAME,
                tools_used=["mouse"],
                steps=steps,
                response=response,
                error=error,
                tool_results={"mouse": {"success": success, "attempt_count": len(attempts)}},
                metadata={
                    "verification_mode": req.verification_mode,
                    "coordinate_space": req.coordinate_space,
                    "label": req.label,
                },
            )

        if hasattr(self.world_model, "record_execution"):
            self.world_model.record_execution(
                task=task,
                task_type=MOUSE_TASK_TYPE,
                success=success,
                model_name=MOUSE_MODEL_NAME,
                route="windows",
                tools_used=["mouse"],
                response=response,
                error=error,
                tool_results={"mouse": {"success": success, "attempt_count": len(attempts)}},
                metadata={
                    "verification_mode": req.verification_mode,
                    "coordinate_space": req.coordinate_space,
                },
                refresh_desktop=False,
            )

    def _active_window(self, refresh: bool) -> dict[str, Any]:
        if not hasattr(self.world_model, "get_state"):
            return {}
        state = self.world_model.get_state(refresh=refresh)
        return state.get("desktop", {}).get("active_window", {}) if isinstance(state, dict) else {}

    def _context_key(self, active_window: dict[str, Any], screen_width: int, screen_height: int) -> str:
        process_name = str(active_window.get("process_name") or "desktop").lower()
        return f"{process_name}|{screen_width}x{screen_height}"

    def _map_coordinates(self, req: MouseActionRequest, screen_width: int, screen_height: int) -> tuple[int, int]:
        space = req.coordinate_space.lower()
        if space == "absolute":
            return round(req.x), round(req.y)
        if space == "normalized":
            x = req.x if req.x <= 1 else req.x / 100
            y = req.y if req.y <= 1 else req.y / 100
            return round(x * screen_width), round(y * screen_height)
        if space == "image":
            source_width, source_height = self._resolve_source_size(req)
            return (
                round((req.x / source_width) * screen_width),
                round((req.y / source_height) * screen_height),
            )
        raise ValueError(f"Unsupported coordinate space: {req.coordinate_space}")

    def _resolve_source_size(self, req: MouseActionRequest) -> tuple[int, int]:
        if req.source_width and req.source_height:
            return req.source_width, req.source_height
        if req.image_path:
            path = Path(req.image_path)
            if not path.is_absolute():
                path = ROOT_DIR / path
            if not path.exists():
                raise FileNotFoundError(f"Image path not found: {path}")
            if ImageGrab is None:
                raise ValueError("Pillow is required to infer image size from image_path.")
            from PIL import Image

            with Image.open(path) as image:
                return image.size
        raise ValueError("Image coordinate space requires source_width/source_height or image_path.")

    def _build_attempt_offsets(self, max_attempts: int, step_px: int, radius_px: int) -> list[tuple[int, int]]:
        offsets: list[tuple[int, int]] = [(0, 0)]
        if max_attempts <= 1:
            return offsets[:max_attempts]

        step_px = max(1, step_px)
        radius_px = max(step_px, radius_px)

        for radius in range(step_px, radius_px + step_px, step_px):
            offsets.extend(
                [
                    (radius, 0),
                    (-radius, 0),
                    (0, radius),
                    (0, -radius),
                    (radius, radius),
                    (radius, -radius),
                    (-radius, radius),
                    (-radius, -radius),
                ]
            )

        unique: list[tuple[int, int]] = []
        for offset in offsets:
            if offset not in unique:
                unique.append(offset)
        return unique[: max_attempts]

    def _capture_verification_region(self, candidate: tuple[int, int], region_px: int):
        half = max(4, region_px // 2)
        bbox = (
            int(candidate[0] - half),
            int(candidate[1] - half),
            int(candidate[0] + half),
            int(candidate[1] + half),
        )
        return self.backend.capture_region(bbox)

    def _verify_attempt(
        self,
        req: MouseActionRequest,
        candidate: tuple[int, int],
        actual: tuple[int, int],
        before_capture: Any,
        before_window: dict[str, Any],
    ) -> dict[str, Any]:
        distance_px = _distance(candidate, actual)
        position_ok = distance_px <= req.tolerance_px
        verification = {
            "mode": req.verification_mode,
            "cursor_position_ok": position_ok,
            "cursor_distance_px": round(distance_px, 2),
            "verified": False,
            "confidence": "low",
        }

        mode = req.verification_mode.lower()
        screen_change_ok = None
        window_ok = None
        color_ok = None

        if mode in {"screen_change", "hybrid"}:
            after_capture = self._capture_verification_region(candidate, req.verify_region_px)
            score = self._screen_change_score(before_capture, after_capture)
            if score is not None:
                screen_change_ok = score >= req.screen_diff_threshold
                verification["screen_change_score"] = round(score, 3)
                verification["screen_change_ok"] = screen_change_ok

        if mode in {"window", "hybrid"} and (req.expected_window_title or req.expected_process_name):
            after_window = self._active_window(refresh=True)
            window_ok = self._window_matches(after_window, req.expected_window_title, req.expected_process_name)
            verification["window_ok"] = window_ok
            verification["window_after"] = after_window
        else:
            after_window = before_window

        if mode in {"color", "hybrid"} and req.expected_rgb:
            pixel = self.backend.sample_pixel(actual[0], actual[1])
            verification["sampled_rgb"] = list(pixel) if pixel else None
            if pixel:
                color_ok = _rgb_distance(pixel, req.expected_rgb) <= req.color_tolerance
                verification["color_ok"] = color_ok

        if mode == "none":
            verification["verified"] = True
            verification["confidence"] = "mechanical"
            return verification
        if mode == "cursor":
            verification["verified"] = position_ok
            verification["confidence"] = "medium" if position_ok else "low"
            if not position_ok:
                verification["reason"] = "cursor_position_mismatch"
            return verification
        if mode == "screen_change":
            verification["verified"] = bool(position_ok and screen_change_ok)
            verification["confidence"] = "high" if verification["verified"] else "low"
            if not verification["verified"]:
                verification["reason"] = "screen_change_not_detected"
            return verification
        if mode == "window":
            verification["verified"] = bool(position_ok and window_ok)
            verification["confidence"] = "high" if verification["verified"] else "low"
            if not verification["verified"]:
                verification["reason"] = "expected_window_not_detected"
            return verification
        if mode == "color":
            verification["verified"] = bool(position_ok and color_ok)
            verification["confidence"] = "high" if verification["verified"] else "low"
            if not verification["verified"]:
                verification["reason"] = "expected_color_not_detected"
            return verification
        if mode == "hybrid":
            secondary = [value for value in [screen_change_ok, window_ok, color_ok] if value is not None]
            secondary_ok = any(secondary) if secondary else True
            verification["verified"] = bool(position_ok and secondary_ok)
            verification["confidence"] = "high" if secondary and secondary_ok and position_ok else "medium" if position_ok else "low"
            if not verification["verified"]:
                verification["reason"] = "hybrid_verification_failed"
            return verification
        raise ValueError(f"Unsupported verification mode: {req.verification_mode}")

    def _screen_change_score(self, before_capture: Any, after_capture: Any) -> Optional[float]:
        if before_capture is None or after_capture is None:
            return None
        if ImageChops is None or ImageStat is None:
            return None
        diff = ImageChops.difference(before_capture.convert("RGB"), after_capture.convert("RGB"))
        stat = ImageStat.Stat(diff)
        return float(sum(stat.mean) / len(stat.mean))

    def _window_matches(
        self,
        active_window: dict[str, Any],
        expected_title: Optional[str],
        expected_process: Optional[str],
    ) -> bool:
        title = str(active_window.get("title") or "").lower()
        process_name = str(active_window.get("process_name") or "").lower()
        if expected_title and expected_title.lower() not in title:
            return False
        if expected_process and expected_process.lower() not in process_name:
            return False
        return True

    def _build_failure_reason(self, attempts: list[dict[str, Any]]) -> str:
        if not attempts:
            return "ui_coordinate_drift: no attempts executed"
        if all(not attempt["verification"].get("cursor_position_ok") for attempt in attempts):
            return "ui_coordinate_drift: cursor position could not be verified"
        final_reason = attempts[-1].get("reason") or "verification_failed"
        return f"ui_coordinate_drift: {final_reason} after {len(attempts)} attempts"

    def _build_response_text(
        self,
        success: bool,
        req: MouseActionRequest,
        final_attempt: Optional[dict[str, Any]],
        context_key: str,
    ) -> str:
        if not final_attempt:
            return "Mouse execution finished without attempts."
        status = "verified" if success else "failed"
        return (
            f"Mouse {req.action} {status} on profile {context_key}. "
            f"Final target={final_attempt['candidate']['x']},{final_attempt['candidate']['y']} "
            f"actual={final_attempt['actual']['x']},{final_attempt['actual']['y']} "
            f"attempts={final_attempt['attempt']}."
        )

    def _clamp_point(self, x: int, y: int, screen_width: int, screen_height: int) -> tuple[int, int]:
        return (
            max(0, min(screen_width - 1, int(x))),
            max(0, min(screen_height - 1, int(y))),
        )


def build_cli_parser(default_agent: str = "shared_cli") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrated mouse automation with verification and retry.")
    parser.add_argument("x", nargs="?", type=float, help="X coordinate or image X")
    parser.add_argument("y", nargs="?", type=float, help="Y coordinate or image Y")
    parser.add_argument("legacy_action", nargs="?", help="Legacy positional action")
    parser.add_argument("--request-json", help="Structured mouse request as JSON")
    parser.add_argument("--request-file", help="Path to a JSON file with the mouse request")
    parser.add_argument("--action", choices=["move", "click", "right_click", "double_click"])
    parser.add_argument("--coordinate-space", choices=["absolute", "normalized", "image"])
    parser.add_argument("--source-width", type=int)
    parser.add_argument("--source-height", type=int)
    parser.add_argument("--image-path")
    parser.add_argument("--label")
    parser.add_argument("--verify", dest="verification_mode", choices=["none", "cursor", "screen_change", "window", "color", "hybrid"])
    parser.add_argument("--expected-window-title")
    parser.add_argument("--expected-process-name")
    parser.add_argument("--expected-rgb", help="RGB as R,G,B")
    parser.add_argument("--color-tolerance", type=int)
    parser.add_argument("--verify-region-px", type=int)
    parser.add_argument("--screen-diff-threshold", type=float)
    parser.add_argument("--tolerance-px", type=int)
    parser.add_argument("--max-attempts", type=int)
    parser.add_argument("--search-step-px", type=int)
    parser.add_argument("--search-radius-px", type=int)
    parser.add_argument("--move-duration-ms", type=int)
    parser.add_argument("--move-steps", type=int)
    parser.add_argument("--settle-ms", type=int)
    parser.add_argument("--click-pause-ms", type=int)
    parser.add_argument("--profile-key")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--agent", default=default_agent)
    return parser


def request_from_cli_args(args: argparse.Namespace) -> MouseActionRequest:
    payload: dict[str, Any] = {}

    if args.request_file:
        with open(args.request_file, "r", encoding="utf-8") as handle:
            payload.update(json.load(handle))
    if args.request_json:
        payload.update(json.loads(args.request_json))

    if args.x is not None:
        payload["x"] = args.x
    if args.y is not None:
        payload["y"] = args.y
    if args.action:
        payload["action"] = args.action
    elif args.legacy_action:
        payload["action"] = args.legacy_action

    for key in [
        "coordinate_space",
        "source_width",
        "source_height",
        "image_path",
        "label",
        "verification_mode",
        "expected_window_title",
        "expected_process_name",
        "expected_rgb",
        "color_tolerance",
        "verify_region_px",
        "screen_diff_threshold",
        "tolerance_px",
        "max_attempts",
        "search_step_px",
        "search_radius_px",
        "move_duration_ms",
        "move_steps",
        "settle_ms",
        "click_pause_ms",
        "profile_key",
    ]:
        value = getattr(args, key, None)
        if value is not None:
            payload[key] = value

    if args.dry_run:
        payload["dry_run"] = True

    return MouseActionRequest.from_payload(payload)


def main(argv: Optional[list[str]] = None, default_agent: str = "shared_cli") -> int:
    parser = build_cli_parser(default_agent=default_agent)
    args = parser.parse_args(argv)
    request = request_from_cli_args(args)
    tool = MouseAutomationTool(agent_name=args.agent)
    result = tool.execute(request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success") else 1


def _normalize_action(value: str) -> str:
    normalized = value.strip().lower()
    alias_map = {
        "left_click": "click",
        "left": "click",
        "right": "right_click",
        "double": "double_click",
        "doubleclick": "double_click",
    }
    return alias_map.get(normalized, normalized)


def _parse_rgb(value: Any) -> Optional[tuple[int, int, int]]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(int(channel) for channel in value)
    if isinstance(value, str):
        parts = [part for part in re.split(r"[,\s:]+", value.strip()) if part]
        if len(parts) == 3:
            return tuple(int(part) for part in parts)
    raise ValueError("expected_rgb must be provided as R,G,B.")


def _blend(previous: float, observed: float, rate: float) -> float:
    return round(float(previous) + ((float(observed) - float(previous)) * rate), 3)


def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _rgb_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum(math.pow(int(x) - int(y), 2) for x, y in zip(a, b)))


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    return int(value)


def _coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    return float(value)


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _merge_dicts(base: Any, current: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(current, dict):
        return current if current is not None else base
    merged = copy.deepcopy(base)
    for key, value in current.items():
        if key in merged:
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
