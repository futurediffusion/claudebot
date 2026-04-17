from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from adapters.browser_adapter import BrowserAdapter


def _make_config() -> MagicMock:
    cfg = MagicMock()
    cfg.logs_dir = Path(tempfile.mkdtemp())
    cfg.action_allowlist = ["browser"]
    cfg.browser_model = "test-browser-model"
    cfg.anthropic_api_key = "test-key"
    cfg.anthropic_base_url = "http://localhost:11434"
    cfg.max_retries = 1
    cfg.max_steps_browser = 7
    cfg.browser_headless = False
    cfg.browser_cdp_url = None
    cfg.browser_cdp_bootstrap_url = "https://www.freepik.com/pikaso/ai-image-generator"
    cfg.browser_use_vision = "auto"
    cfg.browser_channel = "msedge"
    cfg.browser_executable_path = None
    cfg.browser_user_data_dir = None
    cfg.browser_profile_directory = None
    return cfg


def _install_fake_browser_modules(agent_cls, profile_cls, chat_cls):
    browser_use_mod = ModuleType("browser_use")
    browser_use_mod.__path__ = []
    browser_use_mod.Agent = agent_cls

    browser_pkg = ModuleType("browser_use.browser")
    browser_pkg.__path__ = []

    profile_mod = ModuleType("browser_use.browser.profile")
    profile_mod.BrowserProfile = profile_cls

    llm_pkg = ModuleType("browser_use.llm")
    llm_pkg.__path__ = []

    anthropic_pkg = ModuleType("browser_use.llm.anthropic")
    anthropic_pkg.__path__ = []

    anthropic_chat_mod = ModuleType("browser_use.llm.anthropic.chat")
    anthropic_chat_mod.ChatAnthropic = chat_cls

    return patch.dict(
        sys.modules,
        {
            "browser_use": browser_use_mod,
            "browser_use.browser": browser_pkg,
            "browser_use.browser.profile": profile_mod,
            "browser_use.llm": llm_pkg,
            "browser_use.llm.anthropic": anthropic_pkg,
            "browser_use.llm.anthropic.chat": anthropic_chat_mod,
        },
    )


class TestBrowserAdapter:
    def test_run_uses_direct_freepik_flow_for_one_shot_generation(self):
        cfg = _make_config()
        adapter = BrowserAdapter(cfg)
        task = (
            "En Freepik Pikaso, usa la sesion ya iniciada en Edge. "
            "Escribe este prompt en el campo principal: "
            "'un guerrero futurista en una ciudad andina, cinematic lighting, highly detailed' "
            "y pulsa el boton Generate para crear la imagen. No cierres Edge."
        )

        expected = {
            "success": True,
            "content": "Freepik acepto el prompt y empezo a generar la imagen.",
            "error": None,
        }
        with (
            patch.object(adapter, "_ensure_cdp_ready"),
            patch.object(adapter, "_run_freepik_generation", return_value=expected) as direct_flow,
        ):
            result = adapter.run(task)

        direct_flow.assert_called_once_with(
            "un guerrero futurista en una ciudad andina, cinematic lighting, highly detailed"
        )
        assert result == expected

    def test_extract_freepik_prompt_returns_none_when_missing(self):
        adapter = BrowserAdapter(_make_config())
        task = "Abre Freepik y genera una imagen futurista."
        assert adapter._extract_freepik_prompt(task) is None

    def test_run_attaches_to_existing_edge_via_cdp(self):
        cfg = _make_config()
        cfg.browser_cdp_url = "http://127.0.0.1:9242"

        mock_agent_cls = MagicMock()
        mock_profile_cls = MagicMock()
        mock_chat_cls = MagicMock()

        history = SimpleNamespace(
            history=[
                SimpleNamespace(
                    result=[SimpleNamespace(is_done=True, extracted_content="imagen creada")]
                )
            ]
        )
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = history
        mock_agent_cls.return_value = mock_agent
        mock_profile = MagicMock(name="BrowserProfileInstance")
        mock_profile_cls.return_value = mock_profile

        with _install_fake_browser_modules(mock_agent_cls, mock_profile_cls, mock_chat_cls):
            adapter = BrowserAdapter(cfg)
            with patch.object(adapter, "_is_cdp_available", return_value=True):
                result = adapter.run("Genera una imagen en Freepik")

        mock_chat_cls.assert_called_once_with(
            model="test-browser-model",
            api_key="test-key",
            base_url="http://localhost:11434",
        )
        mock_profile_cls.assert_called_once_with(
            headless=False,
            cdp_url="http://127.0.0.1:9242",
        )
        mock_agent_cls.assert_called_once()
        assert mock_agent_cls.call_args.kwargs["browser_profile"] is mock_profile
        assert mock_agent_cls.call_args.kwargs["use_vision"] is False
        assert result == {
            "success": True,
            "content": "imagen creada",
            "error": None,
        }

    def test_run_launches_visible_edge_when_no_cdp_url(self):
        cfg = _make_config()
        cfg.browser_user_data_dir = r"C:\Users\walva\AppData\Local\Microsoft\Edge\User Data"
        cfg.browser_profile_directory = "Default"

        mock_agent_cls = MagicMock()
        mock_profile_cls = MagicMock()
        mock_chat_cls = MagicMock()

        history = SimpleNamespace(
            history=[
                SimpleNamespace(
                    result=[SimpleNamespace(is_done=True, extracted_content="ok")]
                )
            ]
        )
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = history
        mock_agent_cls.return_value = mock_agent
        mock_profile_cls.return_value = MagicMock(name="BrowserProfileInstance")

        with _install_fake_browser_modules(mock_agent_cls, mock_profile_cls, mock_chat_cls):
            adapter = BrowserAdapter(cfg)
            adapter.run("Abre Freepik y genera una imagen")

        assert mock_agent_cls.call_args.kwargs["use_vision"] is False
        mock_chat_cls.assert_called_once_with(
            model="test-browser-model",
            api_key="test-key",
            base_url="http://localhost:11434",
        )
        mock_profile_cls.assert_called_once_with(
            headless=False,
            channel="msedge",
            user_data_dir=r"C:\Users\walva\AppData\Local\Microsoft\Edge\User Data",
            profile_directory="Default",
        )

    def test_run_bootstraps_edge_when_cdp_is_not_ready(self):
        cfg = _make_config()
        cfg.browser_cdp_url = "http://127.0.0.1:9242"

        mock_agent_cls = MagicMock()
        mock_profile_cls = MagicMock()
        mock_chat_cls = MagicMock()

        history = SimpleNamespace(
            history=[SimpleNamespace(result=[SimpleNamespace(is_done=True, extracted_content="ok")])]
        )
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = history
        mock_agent_cls.return_value = mock_agent
        mock_profile_cls.return_value = MagicMock(name="BrowserProfileInstance")

        with _install_fake_browser_modules(mock_agent_cls, mock_profile_cls, mock_chat_cls):
            adapter = BrowserAdapter(cfg)
            with (
                patch.object(adapter, "_is_cdp_available", return_value=False),
                patch.object(adapter, "_edge_is_running", return_value=False),
                patch.object(
                    adapter,
                    "_resolve_edge_executable",
                    return_value=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                ),
                patch.object(adapter, "_wait_for_cdp", return_value=True),
                patch.object(adapter, "_launch_edge_bootstrap_command") as launch,
            ):
                adapter.run("Abre Freepik y genera una imagen")

        assert mock_agent_cls.call_args.kwargs["use_vision"] is False
        launch.assert_called_once_with(
            '& "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" '
            '--remote-debugging-port=9242 '
            '--profile-directory=Default '
            '"https://www.freepik.com/pikaso/ai-image-generator"'
        )
        mock_profile_cls.assert_called_once_with(
            headless=False,
            cdp_url="http://127.0.0.1:9242",
        )

    def test_run_fails_with_clear_command_when_edge_is_already_open_without_cdp(self):
        cfg = _make_config()
        cfg.browser_cdp_url = "http://127.0.0.1:9242"

        adapter = BrowserAdapter(cfg)
        with (
            patch.object(adapter, "_is_cdp_available", return_value=False),
            patch.object(adapter, "_edge_is_running", return_value=True),
            patch.object(
                adapter,
                "_resolve_edge_executable",
                return_value=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ),
        ):
            try:
                adapter.run("Abre Freepik y genera una imagen")
            except RuntimeError as exc:
                message = str(exc)
            else:
                raise AssertionError("Se esperaba RuntimeError cuando Edge ya esta abierto sin CDP.")

        assert "Edge ya esta abierto sin CDP" in message
        assert "--remote-debugging-port=9242" in message
        assert "https://www.freepik.com/pikaso/ai-image-generator" in message

    def test_run_enables_vision_automatically_for_multimodal_models(self):
        cfg = _make_config()
        cfg.browser_model = "qwen3-vl:30b"

        mock_agent_cls = MagicMock()
        mock_profile_cls = MagicMock()
        mock_chat_cls = MagicMock()

        history = SimpleNamespace(
            history=[SimpleNamespace(result=[SimpleNamespace(is_done=True, extracted_content="ok")])]
        )
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = history
        mock_agent_cls.return_value = mock_agent
        mock_profile_cls.return_value = MagicMock(name="BrowserProfileInstance")

        with _install_fake_browser_modules(mock_agent_cls, mock_profile_cls, mock_chat_cls):
            adapter = BrowserAdapter(cfg)
            adapter.run("Abre Freepik y genera una imagen")

        assert mock_agent_cls.call_args.kwargs["use_vision"] is True
