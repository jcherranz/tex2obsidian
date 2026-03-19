"""Tests for Stage 3: Obsidian postprocessing."""

import pytest

from tex2obsidian.postprocess import (
    isolate_display_math,
    fenced_divs_to_callouts,
    normalize_math,
    strip_blank_callout_math_lines,
    separate_consecutive_math_blocks,
    clean_artifacts,
    normalize_math_delimiters,
    tikzcd_to_code_blocks,
    postprocess,
)


class TestIsolateDisplayMath:
    def test_already_isolated(self):
        text = "before\n$$\nx = 1\n$$\nafter"
        assert isolate_display_math(text) == text

    def test_inline_dollar_dollar(self):
        text = "text $$x = 1$$ more"
        result = isolate_display_math(text)
        lines = result.split('\n')
        assert '$$' in lines

    def test_no_math(self):
        text = "just plain text"
        assert isolate_display_math(text) == text


class TestFencedDivsToCallouts:
    def test_theorem(self, default_config):
        text = "::: {.theorem}\nContent here.\n:::"
        result = fenced_divs_to_callouts(text, default_config)
        assert "> [!thm] Theorem" in result
        assert "> Content here." in result

    def test_definition(self, default_config):
        text = "::: {.definition}\nA def.\n:::"
        result = fenced_divs_to_callouts(text, default_config)
        assert "> [!def] Definition" in result

    def test_proof(self, default_config):
        text = "::: {.proof}\nProof body.\n:::"
        result = fenced_divs_to_callouts(text, default_config)
        assert "> [!proof] Proof" in result

    def test_center_unwrapped(self, default_config):
        text = "::: {.center}\nCentered content.\n:::"
        result = fenced_divs_to_callouts(text, default_config)
        assert "Centered content." in result
        assert "[!" not in result

    def test_blank_line_in_callout(self, default_config):
        text = "::: {.theorem}\nLine 1.\n\nLine 2.\n:::"
        result = fenced_divs_to_callouts(text, default_config)
        assert ">" in result  # blank lines become >

    def test_unknown_class(self, default_config):
        text = "::: {.mystery}\nContent.\n:::"
        result = fenced_divs_to_callouts(text, default_config)
        assert "> [!mystery] Mystery" in result


class TestNormalizeMath:
    def test_align_star(self):
        assert r"\begin{aligned}" in normalize_math(r"\begin{align*}")
        assert r"\end{aligned}" in normalize_math(r"\end{align*}")

    def test_gather_star(self):
        assert r"\begin{gathered}" in normalize_math(r"\begin{gather*}")
        assert r"\end{gathered}" in normalize_math(r"\end{gather*}")


class TestStripBlankCalloutMathLines:
    def test_removes_blank_in_math(self):
        text = "> $$\n>\n> x = 1\n> $$"
        result = strip_blank_callout_math_lines(text)
        assert ">\n" not in result.split("> $$")[1].split("> $$")[0]

    def test_preserves_outside_math(self):
        text = "> text\n>\n> more"
        assert strip_blank_callout_math_lines(text) == text


class TestSeparateConsecutiveMathBlocks:
    def test_inserts_separator(self):
        text = "> $$\n> $$"
        result = separate_consecutive_math_blocks(text)
        lines = result.split('\n')
        assert len(lines) == 3
        assert lines[1] == '>'


class TestCleanArtifacts:
    def test_qed_symbols(self):
        for sym in ['\u25fb', '\u25a1', '\u25fc']:
            assert clean_artifacts(f"text{sym}more") == "textmore"

    def test_heading_attributes(self):
        result = clean_artifacts("## Title {#sec:foo .unnumbered}")
        assert "{#" not in result

    def test_collapse_blank_lines(self):
        result = clean_artifacts("a\n\n\n\nb")
        assert result == "a\n\nb"

    def test_trailing_whitespace(self):
        result = clean_artifacts("text   \nmore  ")
        assert "   " not in result


class TestNormalizeMathDelimiters:
    def test_callout_indented(self):
        assert normalize_math_delimiters(">   $$") == "> $$"

    def test_bare_indented(self):
        assert normalize_math_delimiters("   $$") == "$$"

    def test_normal_line_untouched(self):
        assert normalize_math_delimiters("> some text") == "> some text"


class TestTikzcdToCodeBlocks:
    def test_basic_tikzcd(self):
        text = "$$\n\\begin{tikzcd}\nA \\arrow[r] & B\n\\end{tikzcd}\n$$"
        result = tikzcd_to_code_blocks(text)
        assert "```tikz" in result
        assert "\\begin{document}" in result
        assert "\\end{document}" in result
        assert "\\usepackage{tikz-cd}" in result

    def test_callout_tikzcd(self):
        text = "> $$\n> \\begin{tikzcd}\n> A \\arrow[r] & B\n> \\end{tikzcd}\n> $$"
        result = tikzcd_to_code_blocks(text)
        assert "```tikz" in result

    def test_non_tikzcd_preserved(self):
        text = "$$\nx = 1\n$$"
        assert tikzcd_to_code_blocks(text) == text


class TestPostprocess:
    def test_full_pipeline(self, default_config):
        text = "::: {.theorem}\nLet $x = 1$.\n:::\n\n$$\nx = 1\n$$"
        result = postprocess(text, default_config)
        assert "> [!thm] Theorem" in result
        assert "$$" in result
        assert result.endswith('\n')
