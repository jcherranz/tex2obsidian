"""Integration tests requiring pandoc."""

import shutil
import pytest

from tex2obsidian.preprocess import preprocess
from tex2obsidian.pandoc import run_pandoc, check_pandoc
from tex2obsidian.postprocess import postprocess


pytestmark = pytest.mark.pandoc

needs_pandoc = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc not installed"
)


@needs_pandoc
class TestFullPipeline:
    def test_end_to_end(self, schuller_config, sample_tex):
        preprocessed = preprocess(sample_tex, schuller_config)
        pandoc_md = run_pandoc(preprocessed, schuller_config)
        final = postprocess(pandoc_md, schuller_config)

        # Verify key transformations
        assert "> [!def] Definition" in final
        assert r"\mathcal{O}" in final or "mathcal" in final
        assert r"\subseteq" in final or "subseteq" in final
        assert "$$" in final
        assert final.endswith('\n')

    def test_pandoc_version(self):
        version = check_pandoc()
        assert version is not None
        assert "pandoc" in version.lower()

    def test_macro_expansion_in_pipeline(self, schuller_config):
        tex = r"$\R$ is the reals and $\Z$ the integers."
        preprocessed = preprocess(tex, schuller_config)
        assert r"\mathbb{R}" in preprocessed
        assert r"\mathbb{Z}" in preprocessed
        pandoc_md = run_pandoc(preprocessed, schuller_config)
        assert "mathbb" in pandoc_md

    def test_theorem_callout(self, schuller_config):
        tex = r"\bt If $x > 0$ then $x^2 > 0$. \et"
        preprocessed = preprocess(tex, schuller_config)
        pandoc_md = run_pandoc(preprocessed, schuller_config)
        final = postprocess(pandoc_md, schuller_config)
        assert "[!thm]" in final
