"""Stage 3: Obsidian post-processor.

Converts pandoc fenced divs to Obsidian callouts,
isolates display math onto its own lines,
normalizes math environments, and cleans artifacts.
"""

import re

from tex2obsidian.config import Config


def isolate_display_math(text):
    """Ensure $$ is always on its own line."""
    lines = text.split('\n')
    result = []
    for line in lines:
        if '$$' not in line:
            result.append(line)
            continue

        stripped = line.strip()
        if stripped == '$$':
            result.append(line)
            continue

        indent = len(line) - len(line.lstrip())
        prefix = line[:indent]

        parts = stripped.split('$$')
        for i, part in enumerate(parts):
            part_clean = part.strip()
            if part_clean:
                result.append(prefix + part_clean)
            if i < len(parts) - 1:
                result.append(prefix + '$$')

    return '\n'.join(result)


def fenced_divs_to_callouts(text, config: Config):
    """Convert pandoc ::: {.class} ... ::: to Obsidian > [!type] callouts."""
    callout_map = config.callout_map
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^::: \{?\.?(\w+)\}?\s*$', line)
        if m:
            cls = m.group(1)
            i += 1

            if cls == 'center':
                depth = 1
                while i < len(lines) and depth > 0:
                    cur = lines[i]
                    if re.match(r'^::: ', cur):
                        depth += 1
                        result.append(cur)
                    elif cur.strip() == ':::':
                        depth -= 1
                        if depth > 0:
                            result.append(cur)
                    else:
                        result.append(cur)
                    i += 1
                continue

            if cls in callout_map:
                cm = callout_map[cls]
                callout_type = cm["type"]
                callout_name = cm["name"]
            else:
                callout_type = cls
                callout_name = cls.title()

            result.append(f'> [!{callout_type}] {callout_name}')
            depth = 1
            while i < len(lines) and depth > 0:
                cur = lines[i]
                if re.match(r'^::: ', cur):
                    depth += 1
                    result.append(f'> {cur}')
                elif cur.strip() == ':::':
                    depth -= 1
                    if depth > 0:
                        result.append(f'> {cur}')
                elif cur.strip() == '':
                    result.append('>')
                else:
                    result.append(f'> {cur}')
                i += 1
        else:
            result.append(line)
            i += 1
    return '\n'.join(result)


def normalize_math(text):
    """Convert top-level math environments to nested form inside $$."""
    text = text.replace(r'\begin{align*}', r'\begin{aligned}')
    text = text.replace(r'\end{align*}', r'\end{aligned}')
    text = text.replace(r'\begin{gather*}', r'\begin{gathered}')
    text = text.replace(r'\end{gather*}', r'\end{gathered}')
    return text


def strip_blank_callout_math_lines(text):
    """Remove blank > lines inside $$ math blocks within callouts."""
    lines = text.split('\n')
    result = []
    in_callout_math = False
    for line in lines:
        stripped = line.strip()
        if stripped in ('> $$', '>$$'):
            in_callout_math = not in_callout_math
            result.append(line)
        elif in_callout_math and stripped in ('>', '> ', '>'):
            continue
        else:
            result.append(line)
    return '\n'.join(result)


def separate_consecutive_math_blocks(text):
    """Insert blank > line between consecutive > $$ (closing then opening)."""
    lines = text.split('\n')
    result = []
    for i, line in enumerate(lines):
        result.append(line)
        stripped = line.strip()
        if stripped in ('> $$', '>$$') and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            if next_stripped in ('> $$', '>$$'):
                result.append('>')
    return '\n'.join(result)


def clean_artifacts(text):
    """Remove various rendering artifacts from the pandoc output."""
    for sym in ['\u25fb', '\u25a1', '\u25fc']:
        text = text.replace(sym, '')
    text = re.sub(r'\\qedsymbol', '', text)
    text = re.sub(r'\s*\{#[^}]*\}', '', text)
    text = re.sub(r'<figure>\s*</figure>', '', text)
    text = re.sub(r'\\centering\b\s*', '', text)
    text = re.sub(r'\\hfill\b\s*', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(l.rstrip() for l in text.split('\n'))
    return text


def normalize_math_delimiters(text):
    """Strip extra indentation from $$ delimiter lines."""
    lines = text.split('\n')
    result = []
    for line in lines:
        if re.match(r'^\s*>\s*\$\$\s*$', line):
            result.append('> $$')
        elif re.match(r'^\s*\$\$\s*$', line):
            result.append('$$')
        else:
            result.append(line)
    return '\n'.join(result)


def tikzcd_to_code_blocks(text):
    r"""Convert tikzcd inside $$...$$ to ```tikz code blocks."""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped in ('$$', '> $$') and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip().lstrip('> ').strip()
            if next_stripped.startswith('\\begin{tikzcd}'):
                in_callout = stripped == '> $$'
                i += 1
                tikz_lines = []
                while i < len(lines):
                    cur = lines[i].strip()
                    cur_content = cur
                    if in_callout:
                        cur_content = re.sub(r'^>\s?', '', cur)
                    tikz_lines.append(cur_content)
                    if '\\end{tikzcd}' in cur_content:
                        i += 1
                        break
                    i += 1

                if i < len(lines) and lines[i].strip() in ('$$', '> $$'):
                    i += 1

                if in_callout:
                    result.append('')
                result.append('```tikz')
                result.append('\\usepackage{tikz-cd}')
                result.append('\\usepackage{amsmath}')
                result.append('\\usepackage{amssymb}')
                result.append('\\usepackage{amsfonts}')
                result.append('')
                result.append('\\begin{document}')
                for tl in tikz_lines:
                    result.append(tl)
                result.append('\\end{document}')
                result.append('```')
                if in_callout:
                    result.append('')
                continue
        result.append(line)
        i += 1
    return '\n'.join(result)


def postprocess(md_content: str, config: Config) -> str:
    """Full post-processing pipeline."""
    text = isolate_display_math(md_content)
    text = fenced_divs_to_callouts(text, config)
    text = normalize_math(text)
    text = normalize_math_delimiters(text)
    text = strip_blank_callout_math_lines(text)
    text = separate_consecutive_math_blocks(text)
    text = tikzcd_to_code_blocks(text)
    text = clean_artifacts(text)
    return text.strip() + '\n'
