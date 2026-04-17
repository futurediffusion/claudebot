"""Tests para el Orchestrator con mocks de adapters y del cliente Anthropic."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.config import Config
from app.memory import Memory
from app.orchestrator import Orchestrator


def _make_config(
    tmp_path: Path, base_url: str | None = None, model_name: str = "test-model"
) -> Config:
    cfg = MagicMock(spec=Config)
    cfg.anthropic_api_key = "test-key"
    cfg.anthropic_base_url = base_url
    cfg.model_name = model_name
    cfg.orchestrator_model = model_name
    cfg.worker_root = tmp_path
    cfg.logs_dir = tmp_path / "logs"
    cfg.logs_dir.mkdir()
    cfg.playbooks_dir = tmp_path / "playbooks"
    cfg.playbooks_dir.mkdir()
    cfg.tasks_dir = tmp_path / "tasks"
    cfg.tasks_dir.mkdir()
    cfg.memory_file = tmp_path / "memory.json"
    cfg.max_retries = 1
    cfg.max_steps_windows = 25
    cfg.max_steps_browser = 100
    cfg.action_allowlist = ["browser", "files", "data"]
    cfg.browser_headless = False
    cfg.browser_cdp_url = None
    cfg.browser_channel = "msedge"
    cfg.browser_executable_path = None
    cfg.browser_user_data_dir = None
    cfg.browser_profile_directory = None
    return cfg


_DECOMPOSE_RESPONSE = json.dumps(
    [
        {
            "index": 0,
            "description": "Escribir archivo de prueba",
            "adapter": "files",
            "params": {
                "op": "write",
                "path": "tasks/output/test.txt",
                "content": "ok",
            },
        },
    ]
)

_DECOMPOSE_RESPONSE_TWO = json.dumps(
    [
        {"index": 0, "description": "Abrir URL", "adapter": "browser", "params": {}},
        {
            "index": 1,
            "description": "Mover archivo",
            "adapter": "files",
            "params": {"op": "move", "src": "tasks/a.txt", "dst": "tasks/b.txt"},
        },
    ]
)


def _mock_anthropic_response(text: str) -> MagicMock:
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


class TestOrchestrator:
    def _make_orchestrator(self, tmp_path, decompose_text=_DECOMPOSE_RESPONSE):
        cfg = _make_config(tmp_path)
        memory = Memory(cfg.memory_file)
        with patch("app.orchestrator.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = _mock_anthropic_response(
                decompose_text
            )
            mock_client_cls.return_value = mock_client
            orch = Orchestrator(cfg, memory)
            orch._client = mock_client
        return orch, cfg

    def test_full_success_saves_playbook(self, tmp_path):
        orch, cfg = self._make_orchestrator(tmp_path)
        orch._skills["files"] = MagicMock()
        orch._skills["files"].run.return_value = {"success": True, "content": "ok"}

        success = orch.run("t001", "Mover un archivo")
        assert success is True

        playbooks = list(cfg.playbooks_dir.glob("*.json"))
        assert len(playbooks) == 1
        data = json.loads(playbooks[0].read_text())
        assert data["task_id"] == "t001"
        assert data["subtasks"][0]["status"] == "success"

    def test_retry_on_first_failure_then_success(self, tmp_path):
        orch, _ = self._make_orchestrator(tmp_path)
        call_count = {"n": 0}

        def flaky_run(task, params=None):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("error temporal")
            return {"success": True, "content": "ok"}

        orch._skills["files"] = MagicMock()
        orch._skills["files"].run.side_effect = flaky_run

        success = orch.run("t002", "Tarea con fallo temporal")
        assert success is True
        assert call_count["n"] == 2

    def test_all_retries_fail(self, tmp_path):
        orch, cfg = self._make_orchestrator(tmp_path)
        orch._skills["files"] = MagicMock()
        orch._skills["files"].run.side_effect = RuntimeError("fallo permanente")

        success = orch.run("t003", "Tarea que siempre falla")
        assert success is False
        assert not list(cfg.playbooks_dir.glob("*.json"))

    def test_two_subtasks_both_succeed(self, tmp_path):
        orch, cfg = self._make_orchestrator(tmp_path, _DECOMPOSE_RESPONSE_TWO)
        orch._skills["browser"] = MagicMock()
        orch._skills["browser"].run.return_value = {"success": True, "content": "pagina"}
        orch._skills["files"] = MagicMock()
        orch._skills["files"].run.return_value = {"success": True, "content": "movido"}

        success = orch.run("t004", "Descargar y mover")
        assert success is True

        data = json.loads(list(cfg.playbooks_dir.glob("*.json"))[0].read_text())
        assert len(data["subtasks"]) == 2

    def test_unknown_adapter_raises(self, tmp_path):
        bad_response = json.dumps(
            [
                {"index": 0, "description": "algo", "adapter": "malware", "params": {}},
            ]
        )
        orch, _ = self._make_orchestrator(tmp_path, bad_response)

        success = orch.run("t005", "Tarea con adaptador invalido")
        assert success is False

    def test_simple_spanish_summary_uses_rule_based_decompose(self, tmp_path):
        orch, _ = self._make_orchestrator(tmp_path)
        orch._client.messages.create.side_effect = AssertionError("LLM no deberia usarse")

        subtasks = orch._decompose(
            "lee tasks/info.txt y resumelo en tasks/output/resumen.txt"
        )

        assert len(subtasks) == 1
        assert subtasks[0].adapter == "data"
        assert subtasks[0].params == {
            "op": "summarize",
            "src": "tasks/info.txt",
            "dst": "tasks/output/resumen.txt",
        }

    def test_simple_spanish_copy_uses_rule_based_decompose(self, tmp_path):
        orch, _ = self._make_orchestrator(tmp_path)
        orch._client.messages.create.side_effect = AssertionError("LLM no deberia usarse")

        subtasks = orch._decompose(
            "copia tasks/tests/doc.txt a tasks/output/doc_backup.txt"
        )

        assert len(subtasks) == 1
        assert subtasks[0].adapter == "files"
        assert subtasks[0].params == {
            "op": "copy",
            "src": "tasks/tests/doc.txt",
            "dst": "tasks/output/doc_backup.txt",
        }

    def test_llm_output_params_are_normalized(self, tmp_path):
        alias_response = json.dumps(
            [
                {
                    "index": 0,
                    "description": "Leer archivo de entrada",
                    "adapter": "filesystem",
                    "params": {"op": "leer", "src": "tasks/a.txt"},
                },
            ]
        )
        orch, _ = self._make_orchestrator(tmp_path, alias_response)

        subtasks = orch._decompose("revisa tasks/a.txt")

        assert len(subtasks) == 1
        assert subtasks[0].adapter == "files"
        assert subtasks[0].params == {"op": "read", "path": "tasks/a.txt"}

    def test_invalid_llm_params_raise_before_execution(self, tmp_path):
        invalid_response = json.dumps(
            [
                {
                    "index": 0,
                    "description": "Escribir archivo",
                    "adapter": "files",
                    "params": {"op": "write"},
                },
            ]
        )
        orch, _ = self._make_orchestrator(tmp_path, invalid_response)

        with pytest.raises(ValueError, match="files.write requiere 'path'"):
            orch._decompose("escribe algo")

    def test_model_name_from_env_used_as_orchestrator_model(self, tmp_path):
        cfg = _make_config(tmp_path, model_name="minimax-m2.7:cloud")
        assert cfg.orchestrator_model == "minimax-m2.7:cloud"
        assert cfg.model_name == "minimax-m2.7:cloud"

    def test_base_url_passed_to_anthropic_client(self, tmp_path):
        cfg = _make_config(tmp_path, base_url="http://localhost:11434")
        memory = Memory(cfg.memory_file)

        with patch("app.orchestrator.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = _mock_anthropic_response(
                _DECOMPOSE_RESPONSE
            )
            mock_client_cls.return_value = mock_client
            Orchestrator(cfg, memory)
            call_kwargs = mock_client_cls.call_args.kwargs
            assert call_kwargs.get("base_url") == "http://localhost:11434"

    def test_no_base_url_when_none(self, tmp_path):
        cfg = _make_config(tmp_path, base_url=None)
        memory = Memory(cfg.memory_file)

        with patch("app.orchestrator.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            Orchestrator(cfg, memory)
            call_kwargs = mock_client_cls.call_args.kwargs
            assert "base_url" not in call_kwargs
