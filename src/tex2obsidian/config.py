"""Load and merge TOML configuration with built-in profiles."""

import tomllib
from importlib import resources
from pathlib import Path


class Config:
    """Merged configuration from profile defaults + user overrides."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    @property
    def source_dir(self) -> Path:
        return Path(self._data["paths"]["source_dir"]).expanduser()

    @property
    def target_dir(self) -> Path:
        return Path(self._data["paths"]["target_dir"]).expanduser()

    @property
    def pandoc_settings(self) -> dict:
        return self._data.get("pandoc", {})

    @property
    def callout_map(self) -> dict:
        return self._data.get("callouts", {})

    @property
    def env_macros(self) -> list[tuple[str, str]]:
        raw = self._data.get("macros", {}).get("env", [])
        return [(m["cmd"], m["expansion"]) for m in raw]

    @property
    def math_macros(self) -> list[tuple[str, str]]:
        raw = self._data.get("macros", {}).get("math", [])
        return [(m["cmd"], m["expansion"]) for m in raw]

    @property
    def tikz_symbols(self) -> list[tuple[str, str]]:
        raw = self._data.get("macros", {}).get("tikz_symbols", [])
        return [(m["cmd"], m["expansion"]) for m in raw]

    @property
    def file_map(self) -> dict[str, str]:
        files = self._data.get("files", [])
        return {f["source"]: f["target"] for f in files}

    @property
    def splice_marker(self) -> str:
        return self._data.get("splice", {}).get("marker", "### Full Lecture Content")

    @property
    def fix_notable_passages(self) -> bool:
        return self._data.get("splice", {}).get("fix_notable_passages", False)

    @property
    def preamble_theorem_styles(self) -> dict:
        return self._data.get("preamble", {}).get("theorem_styles", {})


def _load_builtin_profile(name: str) -> dict:
    """Load a built-in profile TOML from the package."""
    profile_dir = resources.files("tex2obsidian") / "profiles"
    profile_path = profile_dir / f"{name}.toml"
    return tomllib.loads(profile_path.read_text(encoding="utf-8"))


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Lists are replaced, not appended."""
    merged = base.copy()
    for key, val in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = _deep_merge(merged[key], val)
        else:
            merged[key] = val
    return merged


def load_config(path: Path | None = None) -> Config:
    """Load config from a TOML file, merging over profile defaults.

    Resolution order:
    1. Built-in default.toml
    2. Named profile (if config specifies profile = "...")
    3. User TOML overrides
    """
    # Start with built-in defaults
    data = _load_builtin_profile("default")

    if path is not None:
        user_data = tomllib.loads(path.read_text(encoding="utf-8"))
        # Layer in named profile if specified
        profile_name = user_data.get("profile")
        if profile_name:
            profile_data = _load_builtin_profile(profile_name)
            data = _deep_merge(data, profile_data)
        # Layer in user overrides
        data = _deep_merge(data, user_data)
    return Config(data)


def resolve_lua_filter() -> Path:
    """Return the filesystem path to the bundled Lua filter."""
    filter_dir = resources.files("tex2obsidian") / "pandoc_filters"
    filter_path = filter_dir / "unwrap_theorem_emph.lua"
    # For installed packages, we may need to extract to a temp path.
    # importlib.resources.as_file handles this, but for editable installs
    # the path is already on disk.
    return Path(str(filter_path))


def generate_preamble(config: Config) -> str:
    """Build a minimal LaTeX preamble from theorem style definitions."""
    lines = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb,amsthm}",
        "",
    ]
    styles = config.preamble_theorem_styles
    for style_name, envs in styles.items():
        lines.append(f"\\theoremstyle{{{style_name}}}")
        for env in envs:
            # Use starred (unnumbered) for definition, notation, solution, note
            if env in ("definition", "notation", "solution", "note"):
                lines.append(f"\\newtheorem*{{{env}}}{{{env.title()}}}")
            else:
                # Numbered, sharing the theorem counter
                if env == "theorem":
                    lines.append(f"\\newtheorem{{{env}}}{{{env.title()}}}")
                else:
                    lines.append(f"\\newtheorem{{{env}}}[theorem]{{{env.title()}}}")
        lines.append("")

    lines.append(r"\begin{document}")
    return "\n".join(lines) + "\n"
