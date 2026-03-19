"""Tests for config loading and profile merging."""

import pytest
from pathlib import Path

from tex2obsidian.config import load_config, resolve_lua_filter, generate_preamble, Config


class TestLoadConfig:
    def test_defaults_only(self):
        config = load_config(None)
        assert isinstance(config, Config)
        assert config.callout_map  # should have defaults

    def test_schuller_profile(self, schuller_config):
        assert len(schuller_config.env_macros) > 20
        assert len(schuller_config.math_macros) > 60
        assert len(schuller_config.file_map) == 26

    def test_callout_map(self, schuller_config):
        cm = schuller_config.callout_map
        assert "theorem" in cm
        assert cm["theorem"]["type"] == "thm"
        assert cm["definition"]["type"] == "def"

    def test_splice_marker(self, schuller_config):
        assert schuller_config.splice_marker == "### Full Lecture Content"

    def test_fix_notable_passages(self, schuller_config):
        assert schuller_config.fix_notable_passages is True

    def test_user_override(self, tmp_path):
        toml = tmp_path / "test.toml"
        toml.write_text(
            '[paths]\nsource_dir = "/custom/src"\ntarget_dir = "/custom/tgt"\n'
            '[splice]\nmarker = "### Custom Marker"\n',
            encoding='utf-8',
        )
        config = load_config(toml)
        assert str(config.source_dir) == "/custom/src"
        assert config.splice_marker == "### Custom Marker"

    def test_profile_plus_override(self, tmp_path):
        toml = tmp_path / "test.toml"
        toml.write_text(
            'profile = "schuller"\n\n[paths]\nsource_dir = "/my/src"\ntarget_dir = "/my/tgt"\n',
            encoding='utf-8',
        )
        config = load_config(toml)
        # Has schuller macros
        assert len(config.env_macros) > 20
        # But custom paths
        assert str(config.source_dir) == "/my/src"


class TestResolveLuaFilter:
    def test_filter_exists(self):
        path = resolve_lua_filter()
        assert path.name == "unwrap_theorem_emph.lua"
        assert path.exists()


class TestGeneratePreamble:
    def test_contains_theorem_defs(self, default_config):
        preamble = generate_preamble(default_config)
        assert r"\documentclass{article}" in preamble
        assert r"\newtheorem{theorem}" in preamble
        assert r"\newtheorem*{definition}" in preamble
        assert r"\begin{document}" in preamble


class TestConfigProperties:
    def test_pandoc_settings(self, default_config):
        settings = default_config.pandoc_settings
        assert settings["from_format"] == "latex"
        assert "wrap" in settings

    def test_tikz_symbols(self, schuller_config):
        syms = schuller_config.tikz_symbols
        assert len(syms) == 4
        cmds = [s[0] for s in syms]
        assert "\\halfWedge" in cmds

    def test_preamble_theorem_styles(self, default_config):
        styles = default_config.preamble_theorem_styles
        assert "plain" in styles
        assert "theorem" in styles["plain"]
