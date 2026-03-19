"""Stage 2: Pandoc subprocess wrapper."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from tex2obsidian.config import Config, resolve_lua_filter


def check_pandoc() -> str | None:
    """Return pandoc version string, or None if not found."""
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        return None
    result = subprocess.run(
        [pandoc, "--version"], capture_output=True, text=True
    )
    first_line = result.stdout.split("\n")[0] if result.stdout else ""
    return first_line


def run_pandoc(preprocessed_tex: str, config: Config) -> str:
    """Run pandoc on preprocessed LaTeX, return markdown output.

    Raises RuntimeError on pandoc failure.
    """
    settings = config.pandoc_settings
    from_fmt = settings.get("from_format", "latex")
    to_fmt = settings.get(
        "to_format",
        "markdown+fenced_divs+pipe_tables"
        "-simple_tables-multiline_tables-grid_tables"
        "+tex_math_dollars"
    )
    wrap = settings.get("wrap", "none")
    timeout = settings.get("timeout", 120)

    lua_filter = resolve_lua_filter()

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.tex', delete=False, encoding='utf-8'
    ) as f:
        f.write(preprocessed_tex)
        tmp_path = Path(f.name)

    try:
        cmd = [
            'pandoc',
            '-f', from_fmt,
            '-t', to_fmt,
            f'--wrap={wrap}',
            '--lua-filter', str(lua_filter),
            str(tmp_path),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise RuntimeError(f"pandoc failed: {result.stderr}")
        return result.stdout
    finally:
        tmp_path.unlink(missing_ok=True)
