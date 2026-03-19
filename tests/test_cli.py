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

    def test_convert_with_profile_no_config(self, tmp_path, monkeypatch):
        """convert --profile schuller should not crash even without a config file."""
        monkeypatch.chdir(tmp_path)
        # Will fail because no .tex files exist, but should not crash on config loading
        result = main(["convert", "--profile", "schuller"])
        # All 26 files missing = 26 failures
        assert result == 1

    def test_bare_invocation_with_args(self, tmp_path, monkeypatch):
        """tex2obsidian --dry-run should default to convert --dry-run."""
        monkeypatch.chdir(tmp_path)
        result = main(["--dry-run"])
        assert result == 1  # no file mappings, but should not crash

    def test_bare_invocation_with_file(self, tmp_path, monkeypatch):
        """tex2obsidian file.tex should default to convert file.tex."""
        monkeypatch.chdir(tmp_path)
        result = main(["file.tex"])
        assert result == 1  # no config, but should not crash
