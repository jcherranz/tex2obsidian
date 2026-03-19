"""Stage 1: LaTeX pre-processor.

Expands custom macros, converts IEEEeqnarray to aligned,
handles TikZ symbols, strips comments and index entries.
Wraps output in a minimal LaTeX document pandoc can parse.
"""

import re

from tex2obsidian.config import Config, generate_preamble


POSTAMBLE = "\n\\end{document}\n"


# ---------- helpers ----------

def find_brace_group(text, start):
    """Find content between matched braces starting at text[start] == '{'.
    Returns (content, end_pos) or (None, start) on failure.
    """
    if start >= len(text) or text[start] != '{':
        return None, start
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '\\':
            i += 2
            continue
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    return None, start


def _strip_cmd_with_braces(text, cmd):
    """Remove all occurrences of \\cmd{...}, handling nested braces."""
    target = '\\' + cmd + '{'
    while target in text:
        idx = text.find(target)
        brace_start = idx + len(target) - 1
        _, end = find_brace_group(text, brace_start)
        if end > brace_start:
            text = text[:idx] + text[end:]
        else:
            break
    return text


# ---------- pipeline steps ----------

def strip_comments(text):
    """Remove LaTeX comments (% to end of line, but not escaped \\%)."""
    lines = text.split('\n')
    result = []
    for line in lines:
        cleaned = re.sub(r'(?<!\\)%.*$', '', line)
        result.append(cleaned)
    return '\n'.join(result)


def strip_index(text):
    r"""Remove \index{...} entries, handling nested braces."""
    return _strip_cmd_with_braces(text, 'index')


def strip_label(text):
    r"""Remove \label{...} entries, handling nested braces."""
    return _strip_cmd_with_braces(text, 'label')


def expand_shortcut(text, cmd, expansion):
    """Expand a single macro with word-boundary matching."""
    pattern = re.escape(cmd) + r'(?![a-zA-Z@])'
    return re.sub(pattern, lambda m: expansion, text)


def expand_all_macros(text, config: Config):
    """Expand all environment and math shortcuts from config."""
    for cmd, expansion in config.env_macros:
        text = expand_shortcut(text, cmd, expansion)
    for cmd, expansion in config.math_macros:
        text = expand_shortcut(text, cmd, expansion)
    return text


def convert_ieeeqnarray(text):
    """Convert IEEEeqnarray* environments to equation* + aligned."""
    while '\\IEEEeqnarraymulticol' in text:
        idx = text.find('\\IEEEeqnarraymulticol')
        end = idx + len('\\IEEEeqnarraymulticol')
        _, end = find_brace_group(text, end)
        _, end = find_brace_group(text, end)
        content, end = find_brace_group(text, end)
        if content is not None:
            text = text[:idx] + content + text[end:]
        else:
            break

    text = re.sub(
        r'\\begin\{IEEEeqnarray\*?\}\{[^}]*\}',
        lambda m: '\\begin{equation*}\n\\begin{aligned}',
        text
    )
    text = re.sub(
        r'\\end\{IEEEeqnarray\*?\}',
        lambda m: '\\end{aligned}\n\\end{equation*}',
        text
    )
    return text


def handle_tikz_symbols(text, config: Config):
    """Replace TikZ-defined symbols with standard LaTeX equivalents."""
    for cmd, expansion in config.tikz_symbols:
        pattern = re.escape(cmd) + r'(?![a-zA-Z])'
        text = re.sub(pattern, lambda m, e=expansion: e, text)
    return text


def expand_tvb(text):
    r"""Expand \tvb{x}{a}{p} to the tangent vector notation."""
    def replacer(m):
        x, a, p = m.group(1), m.group(2), m.group(3)
        return (f'\\left(\\frac{{\\partial}}'
                f'{{\\partial {x}^{{{a}}}}}\\right)_{{\\!{p}}}')
    return re.sub(r'\\tvb\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}', replacer, text)


def expand_ccancel(text):
    r"""Expand \Ccancel[color]{content} to \cancel{content}."""
    return re.sub(r'\\Ccancel\[[^\]]*\]', lambda m: '\\cancel', text)


def handle_bm(text):
    r"""Replace \bm with \boldsymbol (MathJax compatible)."""
    return re.sub(r'\\bm(?![a-zA-Z@])', lambda m: '\\boldsymbol', text)


def clean_spacing(text):
    """Remove invisible spacing rules that don't render in Obsidian."""
    text = re.sub(r'\\rule\{0pt\}\{[^}]*\}', '', text)
    return text


def preprocess(tex_content: str, config: Config) -> str:
    """Full preprocessing pipeline. Returns a standalone LaTeX document."""
    text = strip_comments(tex_content)
    text = strip_index(text)
    text = strip_label(text)
    text = expand_all_macros(text, config)
    text = convert_ieeeqnarray(text)
    text = handle_tikz_symbols(text, config)
    text = expand_tvb(text)
    text = expand_ccancel(text)
    text = handle_bm(text)
    text = clean_spacing(text)
    text = text.replace('\\begin{equation*}', '\\[')
    text = text.replace('\\end{equation*}', '\\]')
    preamble = generate_preamble(config)
    return preamble + text + POSTAMBLE
