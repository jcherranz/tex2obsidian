This file contains expected postprocess output patterns for golden testing.
The exact output depends on pandoc version, so we test key patterns rather
than exact match.

Expected patterns after full pipeline:
- [!def] Definition callout
- [!thm] Theorem callout
- [!remark] Remark callout
- $$ on own lines
- \mathcal{O} instead of \cO
- \mathbb{R} instead of \R
- \subseteq instead of \se
- \varepsilon instead of \ve
- \begin{aligned} instead of IEEEeqnarray
- No \index or \label
- \boldsymbol instead of \bm
- \mathbb{Z} instead of \Z
