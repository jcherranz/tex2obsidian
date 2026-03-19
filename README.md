# tex2obsidian

Convert LaTeX lecture notes to Obsidian markdown with callouts, display math, and TikZJax diagrams.

## Installation

```bash
git clone <repo-url> && cd tex2obsidian
make setup
```

Requires Python 3.11+ and [pandoc](https://pandoc.org/) on PATH.

## Usage

```bash
# Initialize config in current directory
tex2obsidian init --profile schuller

# Edit tex2obsidian.toml to set your paths
# then:
tex2obsidian convert              # convert all files
tex2obsidian convert 12grassmann.tex  # convert one file
tex2obsidian convert --dry-run    # preview without writing
tex2obsidian check                # validate config + pandoc
```

## How it works

1. **Preprocess**: expand custom macros, convert IEEEeqnarray, handle TikZ symbols, strip comments/index/labels, wrap in minimal LaTeX document
2. **Pandoc**: convert LaTeX to markdown with fenced divs and tex math dollars, using a Lua filter to unwrap theorem italic emphasis
3. **Postprocess**: convert fenced divs to Obsidian callouts, isolate display math, extract tikzcd to code blocks, clean artifacts
4. **Splice**: insert converted content into existing Obsidian .md files at a configurable marker

## Configuration

All corpus-specific settings (macros, file mappings, callout styles, pandoc args) live in TOML profile files. The built-in `schuller` profile covers 26 Schuller physics lectures. Create your own profile for other corpora.

See `src/tex2obsidian/profiles/schuller.toml` for a complete example.

## Development

```bash
make setup       # create venv + install
make test        # unit tests (no pandoc needed)
make test-full   # all tests including pandoc integration
```
