# AGENTS.md

convopus — small Python CLI (src layout, stdlib + platformdirs/tqdm) that converts audio files/directories to Opus (or MP3) by shelling out to ffmpeg. ffmpeg must be on PATH; it is checked at startup and the program exits if missing.

## Commands

```bash
# Setup — uv manages the venv and lockfile
uv sync

# Run (console script defined in pyproject.toml)
uv run convopus <file-or-dir>
uv run python -m convopus <file-or-dir>   # also works (__main__.py)

# Tests — `integration` marker = real ffmpeg conversions, auto-skipped without ffmpeg
uv run pytest                        # everything (~3 s)
uv run pytest -m "not integration"   # fast unit-only loop (<2 s)
uv run pytest --cov                  # with coverage report

# Manual verification of a change against real audio
uv run convopus -k -nm -b 96k <some .flac/.wav file>

# Lint, format, typecheck (no config files — tool defaults are the contract)
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run ty check src/ tests/

# Windows exe build (spec file is intentionally not gitignored)
uvx pyinstaller build.spec   # -> dist/convopus.exe
```

## Gotchas

- **Config**: `convopus/config.py` defines a frozen `Config` dataclass. `load()` (called once in `main()`) creates a missing config with defaults, fills missing keys from defaults, repairs invalid values with a stderr warning, and never exits on bad config. Importing `convopus` has NO side effects — config is read at runtime, not import time. Keys match case-insensitively (legacy UPPERCASE configs still work). Location: platformdirs user config dir (`%LocalAppData%\D221\convopus\config.json` on Windows), overridable via the `CONVOPUS_CONFIG` env var. A one-time migration from the old appdirs roaming location runs automatically.
- **Version single source of truth**: `__version__` literal in `src/convopus/__init__.py`; pyproject reads it via `attr:` and `cli.py` imports it for `--version`. Don't hardcode versions anywhere else.
- **Conversion is one module**: `convopus/convert.py` holds both paths — sequential (`convert_file`/`convert_folder`, through vendored ffpb → per-file progress bars) and multiprocessing (`_convert_file_mt`, direct `subprocess.run` → total progress only). `_ffmpeg_args` builds the argument list once for both; keep the two branches behavior-identical when editing.
- **`--out` path logic is centralized** in `convopus/outpath.py` — `build_output_path` mirrors the input structure under the output dir, `filter_out_dir_files` keeps an out-dir nested inside a scanned tree from being re-converted. Both branches in `convert.py` use it; don't reimplement per path.
- **`ffpb.main(argv=...)` prepends `"ffmpeg"` itself** — args exclude the binary name. The multiprocessing branch runs `subprocess` directly and must add it: `["ffmpeg"] + _ffmpeg_args(...) + ["-loglevel", "error"]`.
- **Never isolate config in tests via APPDATA-style env vars** — on Windows, platformdirs resolves the real profile through the Win32 shell API and ignores them. The autouse `isolated_config` fixture uses the `CONVOPUS_CONFIG` override, which subprocesses inherit.
- **ffmpeg won't overwrite existing outputs** — it prompts `[y/N]` (handled interactively on the sequential path via ffpb; the multiprocessing path errors on refusal). Pre-existing behavior, not a bug.

## CI / release

- Test workflow on every push/PR: ruff check + format check, ty typecheck, pytest with coverage — matrix {ubuntu, windows} × Python {3.10, 3.13}.
- Publishing to PyPI is automatic when a GitHub Release is published (`python-publish.yml` runs `python -m build` + twine upload). CodeQL scans pushes/PRs to main.
