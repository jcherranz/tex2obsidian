"""Splice converted content into existing Obsidian markdown files."""

import re
from pathlib import Path


def fix_notable_passages(text: str) -> str:
    """Remove orphan > $$ and blank > lines from Notable Passages section."""
    np_marker = '### Notable Passages'
    np_idx = text.find(np_marker)
    if np_idx < 0:
        return text

    rest = text[np_idx:]
    end_match = re.search(r'\n---', rest)
    if end_match:
        end_idx = np_idx + end_match.start()
    else:
        end_idx = len(text)

    before = text[:np_idx]
    np_section = text[np_idx:end_idx]
    after = text[end_idx:]

    lines = np_section.split('\n')
    fixed = []
    for line in lines:
        stripped = line.strip()
        if stripped == '> $$':
            continue
        elif stripped in ('>', '> '):
            fixed.append('')
        else:
            fixed.append(line)

    return before + '\n'.join(fixed) + after


def splice(target_path: Path, marker: str, new_content: str,
           fix_passages: bool = False) -> str:
    """Read target .md, find marker, replace everything below it.

    Returns the new full text. Raises ValueError if marker not found.
    """
    md_text = target_path.read_text(encoding='utf-8')
    idx = md_text.find(marker)
    if idx < 0:
        raise ValueError(f"Marker '{marker}' not found in {target_path}")

    above = md_text[:idx]

    if fix_passages:
        above = fix_notable_passages(above)
        above = re.sub(r'(\n---\s*){2,}\n*$', '\n---\n\n---\n\n---\n\n---\n\n', above)

    return above + marker + '\n\n' + new_content
