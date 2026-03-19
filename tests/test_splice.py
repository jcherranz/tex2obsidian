"""Tests for splice module."""

import pytest
from pathlib import Path

from tex2obsidian.splice import splice, fix_notable_passages


class TestFixNotablePassages:
    def test_removes_orphan_dd(self):
        text = "### Notable Passages\n> quote\n> $$\n> next"
        result = fix_notable_passages(text)
        assert "> $$" not in result

    def test_blank_blockquote_to_empty(self):
        text = "### Notable Passages\n> quote\n>\n> next"
        result = fix_notable_passages(text)
        assert "\n\n" in result

    def test_no_marker(self):
        text = "no notable passages here"
        assert fix_notable_passages(text) == text

    def test_stops_at_hr(self):
        text = "### Notable Passages\n> quote\n> $$\n---\nafter"
        result = fix_notable_passages(text)
        assert "after" in result


class TestSplice:
    def test_basic_splice(self, fixtures_dir):
        target = fixtures_dir / "sample_target.md"
        result = splice(target, "### Full Lecture Content", "New content here.\n")
        assert "### Full Lecture Content" in result
        assert "New content here." in result
        assert "Old content" not in result

    def test_preserves_above(self, fixtures_dir):
        target = fixtures_dir / "sample_target.md"
        result = splice(target, "### Full Lecture Content", "New.\n")
        assert "## Summary" in result
        assert "This is the summary section." in result

    def test_missing_marker(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("no marker here", encoding='utf-8')
        with pytest.raises(ValueError, match="Marker.*not found"):
            splice(p, "### Full Lecture Content", "content")

    def test_fix_passages(self, tmp_path):
        content = (
            "### Notable Passages\n> quote\n> $$\n>\n"
            "---\n### Full Lecture Content\nold"
        )
        p = tmp_path / "test.md"
        p.write_text(content, encoding='utf-8')
        result = splice(p, "### Full Lecture Content", "new\n", fix_passages=True)
        assert "> $$" not in result.split("### Full Lecture Content")[0]
