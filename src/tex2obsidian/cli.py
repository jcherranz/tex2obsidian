"""CLI entry point: convert, init, check subcommands."""

import argparse
import sys
from pathlib import Path

from tex2obsidian.config import Config, load_config, resolve_lua_filter
from tex2obsidian.pandoc import check_pandoc, run_pandoc
from tex2obsidian.postprocess import postprocess
from tex2obsidian.preprocess import preprocess
from tex2obsidian.splice import splice


def _find_config(args_config: str | None) -> Path | None:
    """Locate config file: explicit arg > cwd > None."""
    if args_config:
        p = Path(args_config)
        if not p.exists():
            print(f"Error: config file not found: {p}", file=sys.stderr)
            sys.exit(1)
        return p
    cwd = Path.cwd() / "tex2obsidian.toml"
    if cwd.exists():
        return cwd
    return None


def _run_pipeline(tex_file: Path, md_file: Path, config: Config,
                  dry_run: bool = False) -> bool:
    """Run the full conversion pipeline for one lecture."""
    print(f"  {tex_file.name} -> {md_file.name}", end=' ... ')

    tex_content = tex_file.read_text(encoding='utf-8')
    preprocessed = preprocess(tex_content, config)
    pandoc_md = run_pandoc(preprocessed, config)
    final_content = postprocess(pandoc_md, config)

    if dry_run:
        print(f"OK (dry-run, {len(final_content)} chars)")
        return True

    new_text = splice(
        md_file,
        config.splice_marker,
        final_content,
        fix_passages=config.fix_notable_passages,
    )
    md_file.write_text(new_text, encoding='utf-8')
    print(f"OK ({len(final_content)} chars)")
    return True


def cmd_convert(args):
    """Convert .tex files to Obsidian markdown."""
    config_path = _find_config(args.config)
    if config_path is None and args.profile:
        # No config file; write a temporary one referencing the profile
        import tempfile
        toml_content = (
            f'profile = "{args.profile}"\n\n'
            f'[paths]\nsource_dir = "."\ntarget_dir = "."\n'
        )
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.toml', delete=False, encoding='utf-8'
        ) as f:
            f.write(toml_content)
            config_path = Path(f.name)
        try:
            config = load_config(config_path)
        finally:
            config_path.unlink(missing_ok=True)
    else:
        config = load_config(config_path)

    file_map = config.file_map
    if not file_map:
        print("Error: no file mappings defined in config", file=sys.stderr)
        return 1

    if args.files:
        targets = args.files
    else:
        targets = sorted(file_map.keys())

    print(f"Converting {len(targets)} files (dry_run={args.dry_run})\n")

    success = 0
    fail = 0
    for tex_name in targets:
        if tex_name not in file_map:
            print(f"  {tex_name}: UNKNOWN FILE", file=sys.stderr)
            fail += 1
            continue

        tex_file = config.source_dir / tex_name
        md_file = config.target_dir / file_map[tex_name]

        if not tex_file.exists():
            print(f"  {tex_name}: TEX MISSING ({tex_file})", file=sys.stderr)
            fail += 1
            continue
        if not md_file.exists():
            print(f"  {tex_name}: MD MISSING ({md_file})", file=sys.stderr)
            fail += 1
            continue

        try:
            if _run_pipeline(tex_file, md_file, config, dry_run=args.dry_run):
                success += 1
            else:
                fail += 1
        except Exception as e:
            print(f"ERROR: {e}")
            fail += 1

    print(f"\nDone: {success} OK, {fail} failed")
    return 0 if fail == 0 else 1


def cmd_init(args):
    """Write a starter tex2obsidian.toml in the current directory."""
    dest = Path.cwd() / "tex2obsidian.toml"
    if dest.exists() and not args.force:
        print(f"Error: {dest} already exists (use --force to overwrite)", file=sys.stderr)
        return 1

    lines = ['version = 1']
    if args.profile:
        lines.append(f'profile = "{args.profile}"')
    lines.append('')
    lines.append('[paths]')
    lines.append('source_dir = "path/to/latex"')
    lines.append('target_dir = "path/to/obsidian"')
    lines.append('')

    dest.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"Created {dest}")
    if args.profile:
        print(f"Profile '{args.profile}' will be loaded. Edit paths above.")
    return 0


def cmd_check(args):
    """Validate config, paths, and pandoc availability."""
    config_path = _find_config(args.config)
    if config_path is None:
        print("No tex2obsidian.toml found in current directory.", file=sys.stderr)
        print("Run 'tex2obsidian init' to create one.", file=sys.stderr)
        return 1

    print(f"Config: {config_path}")
    config = load_config(config_path)

    ok = True

    # Check paths
    src = config.source_dir
    tgt = config.target_dir
    print(f"Source dir: {src} {'OK' if src.is_dir() else 'MISSING'}")
    print(f"Target dir: {tgt} {'OK' if tgt.is_dir() else 'MISSING'}")
    if not src.is_dir() or not tgt.is_dir():
        ok = False

    # Check pandoc
    version = check_pandoc()
    if version:
        print(f"Pandoc: {version}")
    else:
        print("Pandoc: NOT FOUND")
        ok = False

    # Check Lua filter
    lua = resolve_lua_filter()
    print(f"Lua filter: {lua} {'OK' if lua.exists() else 'MISSING'}")
    if not lua.exists():
        ok = False

    # Check file mappings
    fm = config.file_map
    print(f"File mappings: {len(fm)}")

    # Check macros
    env_count = len(config.env_macros)
    math_count = len(config.math_macros)
    print(f"Macros: {env_count} env, {math_count} math")

    if ok:
        print("\nAll checks passed.")
    else:
        print("\nSome checks failed.", file=sys.stderr)
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='tex2obsidian',
        description='Convert LaTeX lecture notes to Obsidian markdown'
    )
    sub = parser.add_subparsers(dest='command')

    # convert
    p_convert = sub.add_parser('convert', help='Convert .tex files')
    p_convert.add_argument('files', nargs='*', help='.tex filenames to convert (default: all)')
    p_convert.add_argument('--config', help='Path to tex2obsidian.toml')
    p_convert.add_argument('--profile', help='Built-in profile name')
    p_convert.add_argument('--dry-run', action='store_true', help='Preview without writing')

    # init
    p_init = sub.add_parser('init', help='Create starter config')
    p_init.add_argument('--profile', help='Built-in profile to use')
    p_init.add_argument('--force', action='store_true', help='Overwrite existing config')

    # check
    p_check = sub.add_parser('check', help='Validate config and dependencies')
    p_check.add_argument('--config', help='Path to tex2obsidian.toml')

    # Bare invocation (no subcommand) defaults to convert.
    # parse_known_args rejects positional args that aren't valid subcommands,
    # so we catch that and retry with 'convert' prepended.
    effective_argv = argv if argv is not None else sys.argv[1:]
    try:
        args, remaining = parser.parse_known_args(effective_argv)
    except SystemExit:
        args = parser.parse_args(['convert'] + effective_argv)
        remaining = []

    if args.command is None:
        args = parser.parse_args(['convert'] + remaining)

    if args.command == 'convert':
        return cmd_convert(args)
    elif args.command == 'init':
        return cmd_init(args)
    elif args.command == 'check':
        return cmd_check(args)
    else:
        parser.print_help()
        return 0
