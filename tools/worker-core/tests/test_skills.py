"""Tests para FilesSkill y DataSkill."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from skills.data import DataSkill
from skills.files import FilesSkill


def _make_config(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.worker_root = tmp_path
    cfg.logs_dir = tmp_path / "logs"
    cfg.logs_dir.mkdir()
    return cfg


class TestFilesSkillDirect:
    def test_write_and_read(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("output/hello.txt", "hola mundo")
        assert skill.read("output/hello.txt") == "hola mundo"

    def test_move(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("a.txt", "dato")
        skill.move("a.txt", "b.txt")
        assert not (tmp_path / "a.txt").exists()
        assert (tmp_path / "b.txt").read_text() == "dato"

    def test_copy(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("orig.txt", "copia")
        skill.copy("orig.txt", "dest.txt")
        assert (tmp_path / "orig.txt").exists()
        assert (tmp_path / "dest.txt").read_text() == "copia"

    def test_path_traversal_blocked(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        with pytest.raises(PermissionError):
            skill.read("../../etc/passwd")


class TestFilesSkillRun:
    def test_run_write(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        result = skill.run("escribir", {"op": "write", "path": "out.txt", "content": "hola"})
        assert result["success"] is True
        assert (tmp_path / "out.txt").read_text() == "hola"

    def test_run_move(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("src.txt", "x")
        result = skill.run("mover", {"op": "move", "src": "src.txt", "dst": "dst.txt"})
        assert result["success"] is True
        assert (tmp_path / "dst.txt").exists()
        assert not (tmp_path / "src.txt").exists()

    def test_run_copy(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("orig.txt", "y")
        result = skill.run("copiar", {"op": "copy", "src": "orig.txt", "dst": "copia.txt"})
        assert result["success"] is True
        assert (tmp_path / "orig.txt").exists()
        assert (tmp_path / "copia.txt").exists()

    def test_run_read(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("data.txt", "contenido")
        result = skill.run("leer", {"op": "read", "path": "data.txt"})
        assert result["success"] is True
        assert result["content"] == "contenido"

    def test_run_unknown_op(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        with pytest.raises(ValueError, match="operaci"):
            skill.run("algo", {"op": "delete"})

    def test_run_text_fallback_move(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        skill.write("src.txt", "x")
        result = skill.run("move src.txt to dst.txt")
        assert result["success"] is True

    def test_run_text_fallback_unknown(self, tmp_path):
        skill = FilesSkill(_make_config(tmp_path))
        with pytest.raises(ValueError):
            skill.run("delete everything")


class TestDataSkillRun:
    def test_write_summary_via_params(self, tmp_path):
        skill = DataSkill(_make_config(tmp_path))
        result = skill.run(
            "resumen",
            {"op": "write_summary", "path": "logs/summary.txt", "lines": ["linea 1", "linea 2"]},
        )
        assert result["success"] is True
        content = (tmp_path / "logs" / "summary.txt").read_text(encoding="utf-8")
        assert "linea 1" in content
        assert "linea 2" in content

    def test_write_json_via_params(self, tmp_path):
        skill = DataSkill(_make_config(tmp_path))
        result = skill.run(
            "json",
            {"op": "write_json", "path": "out/data.json", "data": {"k": "v"}},
        )
        assert result["success"] is True
        loaded = json.loads((tmp_path / "out" / "data.json").read_text())
        assert loaded == {"k": "v"}

    def test_write_and_read_json_direct(self, tmp_path):
        skill = DataSkill(_make_config(tmp_path))
        skill.write_json("out/data.json", {"key": "value", "num": 42})
        loaded = skill.read_json("out/data.json")
        assert loaded == {"key": "value", "num": 42}

    def test_write_summary_appends(self, tmp_path):
        skill = DataSkill(_make_config(tmp_path))
        skill.write_summary("logs/summary.txt", ["linea 1"])
        skill.write_summary("logs/summary.txt", ["linea 2"])
        content = (tmp_path / "logs" / "summary.txt").read_text(encoding="utf-8")
        assert "linea 1" in content
        assert "linea 2" in content

    def test_read_csv(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
        skill = DataSkill(_make_config(tmp_path))
        rows = skill.read_csv("data.csv")
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"

    def test_data_path_traversal_blocked(self, tmp_path):
        skill = DataSkill(_make_config(tmp_path))
        with pytest.raises(PermissionError):
            skill.write_json("../../outside.json", {"blocked": True})

    def test_unknown_op(self, tmp_path):
        skill = DataSkill(_make_config(tmp_path))
        with pytest.raises(ValueError, match="operaci"):
            skill.run("algo", {"op": "delete_all"})
