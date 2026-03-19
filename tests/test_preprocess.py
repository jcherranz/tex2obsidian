"""Tests for Stage 1: LaTeX preprocessing."""

import pytest

from tex2obsidian.preprocess import (
    strip_comments,
    strip_index,
    strip_label,
    expand_shortcut,
    expand_all_macros,
    convert_ieeeqnarray,
    handle_tikz_symbols,
    expand_tvb,
    expand_ccancel,
    handle_bm,
    clean_spacing,
    find_brace_group,
    preprocess,
)


class TestStripComments:
    def test_removes_comment(self):
        assert strip_comments("hello % world") == "hello "

    def test_preserves_escaped_percent(self):
        assert strip_comments(r"50\% done") == r"50\% done"

    def test_multiline(self):
        result = strip_comments("a % comment\nb % comment2")
        assert result == "a \nb "


class TestStripIndex:
    def test_simple(self):
        assert strip_index(r"\index{topology}rest") == "rest"

    def test_nested_braces(self):
        result = strip_index(r"\index{$\cO_\mathrm{std}$}rest")
        assert result == "rest"

    def test_no_index(self):
        assert strip_index("no index here") == "no index here"


class TestStripLabel:
    def test_simple(self):
        assert strip_label(r"\label{sec:foo}rest") == "rest"


class TestExpandShortcut:
    def test_basic_expansion(self):
        result = expand_shortcut(r"\cO is nice", r"\cO", r"\mathcal{O}")
        assert result == r"\mathcal{O} is nice"

    def test_no_expansion_when_longer(self):
        # \cO should not match \cOther
        result = expand_shortcut(r"\cOther", r"\cO", r"\mathcal{O}")
        assert result == r"\cOther"

    def test_word_boundary(self):
        result = expand_shortcut(r"\bd text", r"\bd", r"\begin{definition}")
        assert result == r"\begin{definition} text"


class TestExpandAllMacros:
    def test_env_shortcuts(self, schuller_config):
        result = expand_all_macros(r"\bd some def \ed", schuller_config)
        assert r"\begin{definition}" in result
        assert r"\end{definition}" in result

    def test_math_shortcuts(self, schuller_config):
        result = expand_all_macros(r"$\cO$ and $\R$", schuller_config)
        assert r"\mathcal{O}" in result
        assert r"\mathbb{R}" in result

    def test_greek(self, schuller_config):
        result = expand_all_macros(r"$\a + \b$", schuller_config)
        assert r"\alpha" in result
        assert r"\beta" in result


class TestFindBraceGroup:
    def test_simple(self):
        content, end = find_brace_group("{hello}", 0)
        assert content == "hello"
        assert end == 7

    def test_nested(self):
        content, end = find_brace_group("{a{b}c}", 0)
        assert content == "a{b}c"

    def test_escaped_brace(self):
        content, end = find_brace_group(r"{a\}b}", 0)
        assert content == r"a\}b"

    def test_no_brace(self):
        content, end = find_brace_group("hello", 0)
        assert content is None


class TestConvertIEEEeqnarray:
    def test_basic(self):
        tex = r"\begin{IEEEeqnarray*}{rCl}" "\n" r"a &=& b" "\n" r"\end{IEEEeqnarray*}"
        result = convert_ieeeqnarray(tex)
        assert r"\begin{equation*}" in result
        assert r"\begin{aligned}" in result
        assert r"\end{aligned}" in result
        assert r"\end{equation*}" in result

    def test_multicol(self):
        tex = r"\IEEEeqnarraymulticol{3}{l}{content here}"
        result = convert_ieeeqnarray(tex)
        assert result == "content here"


class TestHandleTikzSymbols:
    def test_halfwedge(self, schuller_config):
        result = handle_tikz_symbols(r"\halfWedge rest", schuller_config)
        assert r"\curlywedge" in result

    def test_no_partial_match(self, schuller_config):
        result = handle_tikz_symbols(r"\halfWedgeExtra", schuller_config)
        assert result == r"\halfWedgeExtra"


class TestExpandTvb:
    def test_basic(self):
        result = expand_tvb(r"\tvb{x}{a}{p}")
        assert r"\partial" in result
        assert "x" in result
        assert "a" in result
        assert "p" in result


class TestExpandCcancel:
    def test_basic(self):
        result = expand_ccancel(r"\Ccancel[red]{content}")
        assert result == r"\cancel{content}"


class TestHandleBm:
    def test_basic(self):
        result = handle_bm(r"\bm{v}")
        assert result == r"\boldsymbol{v}"

    def test_no_partial(self):
        result = handle_bm(r"\bmExtra")
        assert result == r"\bmExtra"


class TestCleanSpacing:
    def test_invisible_rule(self):
        result = clean_spacing(r"\rule{0pt}{12pt}text")
        assert result == "text"


class TestPreprocess:
    def test_full_pipeline(self, schuller_config):
        tex = r"\bd Let $\cO$ be open. \ed"
        result = preprocess(tex, schuller_config)
        assert r"\documentclass{article}" in result
        assert r"\begin{definition}" in result
        assert r"\end{definition}" in result
        assert r"\mathcal{O}" in result
        assert r"\end{document}" in result

    def test_equation_star_to_brackets(self, schuller_config):
        tex = r"\bse x = 1 \ese"
        result = preprocess(tex, schuller_config)
        assert r"\[" in result
        assert r"\]" in result
        assert r"\begin{equation*}" not in result
