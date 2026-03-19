"""Shared pytest fixtures."""

import pytest
from pathlib import Path

from tex2obsidian.config import load_config


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def schuller_config():
    """Load config with the schuller profile (no user overrides)."""
    # Build a minimal user config that just specifies the profile
    import tempfile
    toml_content = 'profile = "schuller"\n\n[paths]\nsource_dir = "/tmp"\ntarget_dir = "/tmp"\n'
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.toml', delete=False, encoding='utf-8'
    ) as f:
        f.write(toml_content)
        tmp = Path(f.name)
    try:
        return load_config(tmp)
    finally:
        tmp.unlink(missing_ok=True)


@pytest.fixture
def default_config():
    """Load config with just defaults (no profile)."""
    return load_config(None)


@pytest.fixture
def sample_tex(fixtures_dir):
    return (fixtures_dir / "sample_input.tex").read_text(encoding='utf-8')


@pytest.fixture
def sample_expected_md(fixtures_dir):
    return (fixtures_dir / "sample_expected.md").read_text(encoding='utf-8')
