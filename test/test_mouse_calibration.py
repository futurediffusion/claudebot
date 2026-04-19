import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.tools.mouse_calibration import MouseAutomationTool, MouseActionRequest


class DummySelfModel:
    def __init__(self):
        self.calls = []

    def record_execution(self, **kwargs):
        self.calls.append(kwargs)


class DummyEpisodicMemory:
    def __init__(self):
        self.calls = []

    def record_episode(self, **kwargs):
        self.calls.append(kwargs)


class FakeBackend:
    def __init__(self, screen_size=(1920, 1080), actual_offset=(0, 0)):
        self._screen_size = screen_size
        self._actual_offset = actual_offset
        self.position = (0, 0)
        self.click_count = 0
        self.move_history = []

    def screen_size(self):
        return self._screen_size

    def get_position(self):
        return self.position

    def move_to(self, x, y, duration_ms=0, steps=0):
        del duration_ms, steps
        self.move_history.append((x, y))
        self.position = (x + self._actual_offset[0], y + self._actual_offset[1])
        return self.position

    def click(self, action):
        del action
        self.click_count += 1

    def capture_region(self, bbox):
        del bbox
        return None

    def sample_pixel(self, x, y):
        del x, y
        return None


class FakeWorldModel:
    def __init__(self, backend, base_title="Base Window", success_title=None):
        self.backend = backend
        self.base_title = base_title
        self.success_title = success_title
        self.start_calls = []
        self.exec_calls = []

    def get_state(self, refresh=False):
        del refresh
        title = self.base_title
        if self.success_title and self.backend.click_count >= 2:
            title = self.success_title
        return {
            "desktop": {
                "active_window": {
                    "title": title,
                    "process_name": "fakeapp",
                    "pid": 123,
                }
            }
        }

    def record_task_start(self, **kwargs):
        self.start_calls.append(kwargs)

    def record_execution(self, **kwargs):
        self.exec_calls.append(kwargs)


class MouseCalibrationTests(unittest.TestCase):
    def build_tool(self, backend, world_model, tempdir):
        profile_path = Path(tempdir) / "mouse_calibration.json"
        history_path = Path(tempdir) / "mouse_calibration.jsonl"
        return MouseAutomationTool(
            agent_name="test_agent",
            backend=backend,
            profile_path=profile_path,
            history_path=history_path,
            self_model=DummySelfModel(),
            episodic_memory=DummyEpisodicMemory(),
            world_model=world_model,
        )

    def test_image_coordinates_apply_profile_offsets(self):
        with tempfile.TemporaryDirectory() as tempdir:
            backend = FakeBackend()
            world_model = FakeWorldModel(backend)
            tool = self.build_tool(backend, world_model, tempdir)

            profile = tool.store.load_profile()
            profile["global"]["offset_x"] = 2
            profile["global"]["offset_y"] = 3
            profile["contexts"]["fakeapp|1920x1080"] = {
                "offset_x": 10,
                "offset_y": -5,
                "runs": 0,
                "successes": 0,
                "failures": 0,
                "last_error": None,
                "verification_modes": {},
                "context_snapshot": {},
            }
            with open(tool.store.profile_path, "w", encoding="utf-8") as handle:
                json.dump(profile, handle, ensure_ascii=False, indent=2)

            result = tool.execute(
                MouseActionRequest(
                    x=640,
                    y=360,
                    action="move",
                    coordinate_space="image",
                    source_width=1280,
                    source_height=720,
                    verification_mode="cursor",
                )
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["mapped_target"], {"x": 960, "y": 540})
            self.assertEqual(result["calibrated_target"], {"x": 972, "y": 538})
            self.assertEqual(result["actual_position"], {"x": 972, "y": 538})
            self.assertEqual(result["attempt_count"], 1)

    def test_second_attempt_learns_successful_offset(self):
        with tempfile.TemporaryDirectory() as tempdir:
            backend = FakeBackend()
            world_model = FakeWorldModel(backend, success_title="Opened Panel")
            tool = self.build_tool(backend, world_model, tempdir)

            result = tool.execute(
                MouseActionRequest(
                    x=400,
                    y=300,
                    action="click",
                    coordinate_space="absolute",
                    verification_mode="window",
                    expected_window_title="Opened Panel",
                    max_attempts=2,
                    search_step_px=8,
                    search_radius_px=8,
                )
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["attempt_count"], 2)
            self.assertEqual(result["attempts"][1]["search_offset"], {"x": 8, "y": 0})

            profile = tool.store.load_profile()
            context = profile["contexts"]["fakeapp|1920x1080"]
            self.assertGreater(context["offset_x"], 0)
            self.assertEqual(context["successes"], 1)

    def test_position_mismatch_fails_with_coordinate_drift(self):
        with tempfile.TemporaryDirectory() as tempdir:
            backend = FakeBackend(actual_offset=(20, 20))
            world_model = FakeWorldModel(backend)
            tool = self.build_tool(backend, world_model, tempdir)

            result = tool.execute(
                MouseActionRequest(
                    x=100,
                    y=100,
                    action="move",
                    coordinate_space="absolute",
                    verification_mode="cursor",
                    max_attempts=2,
                    search_step_px=8,
                    search_radius_px=8,
                    tolerance_px=2,
                )
            )

            self.assertFalse(result["success"])
            self.assertIn("ui_coordinate_drift", result["error"])
            self.assertEqual(result["attempt_count"], 2)

    def test_dry_run_does_not_update_profile_stats(self):
        with tempfile.TemporaryDirectory() as tempdir:
            backend = FakeBackend()
            world_model = FakeWorldModel(backend)
            tool = self.build_tool(backend, world_model, tempdir)

            result = tool.execute(
                MouseActionRequest(
                    x=0.5,
                    y=0.5,
                    action="move",
                    coordinate_space="normalized",
                    verification_mode="cursor",
                    dry_run=True,
                )
            )

            self.assertTrue(result["success"])
            profile = tool.store.load_profile()
            self.assertEqual(profile["global"]["runs"], 0)
            self.assertEqual(profile["contexts"], {})


if __name__ == "__main__":
    unittest.main()
