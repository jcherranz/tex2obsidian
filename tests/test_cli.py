"""Tests for CLI dispatch and argument handling."""

import pytest
from unittest.mock import patch

from tex2obsidian.cli import main


class TestCliDispatch:
    def test_help_exits(self):
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_init_creates_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = main(["init"])
        assert result == 0
        assert (tmp_path / "tex2obsidian.toml").exists()
        content = (tmp_path / "tex2obsidian.toml").read_text()
        assert "version = 1" in content

    def test_init_with_profile(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = main(["init", "--profile", "schuller"])
        assert result == 0
        content = (tmp_path / "tex2obsidian.toml").read_text()
        assert 'profile = "schuller"' in content

    def test_init_no_overwrite(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tex2obsidian.toml").write_text("existing")
        result = main(["init"])
        assert result == 1

    def test_init_force_overwrite(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tex2obsidian.toml").write_text("existing")
        result = main(["init", "--force"])
        assert result == 0

    def test_check_no_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = main(["check"])
        assert result == 1

    def test_convert_no_config(self, tmp_path, monkeypatch):
        """Convert with no config and no profile should fail gracefully."""
        monkeypatch.chdir(tmp_path)
        # No config file, no profile: load_config(None) returns defaults with no files
        result = main(["convert"])
        assert result == 1  # no file mappings

    def test_convert_missing_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit):
            main(["convert", "--config", "nonexistent.toml"])
