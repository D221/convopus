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
uv run --with pyinstaller pyinstaller build.spec --noconfirm   # -> dist/convopus.exe

# Logo and app icon (re-run only when the mark changes; icon is CC0)
uv run python tools/make_logo.py                                 # -> docs/logo.svg
uv run --with cairosvg --with pillow python tools/make_icon.py   # -> docs/icon.ico
```

## Gotchas

- **Config**: `convopus/config.py` defines a frozen `Config` dataclass. `load()` (called once in `main()`) creates a missing config with defaults, fills missing keys from defaults, repairs invalid values with a stderr warning, and never exits on bad config. Importing `convopus` has NO side effects — config is read at runtime, not import time. Keys match case-insensitively (legacy UPPERCASE configs still work). Location: platformdirs user config dir (`%LocalAppData%\D221\convopus\config.json` on Windows), overridable via the `CONVOPUS_CONFIG` env var. A one-time migration from the old appdirs roaming location runs automatically.
- **Version single source of truth**: `__version__` literal in `src/convopus/__init__.py`; pyproject reads it via `attr:` and `cli.py` imports it for `--version`. Don't hardcode versions anywhere else.
- **Conversion is one module**: `convopus/convert.py` holds both paths — sequential (`convert_file`/`convert_folder`, through vendored ffpb → per-file progress bars) and direct (`_convert_file_direct`, `subprocess.run` → used by the pool and by `--quiet`, total progress only). Both wrappers call `_run_ffmpeg`; `_ffmpeg_args` builds the argument list once for both; keep the two branches behavior-identical when editing.
- **`--out` path logic is centralized** in `convopus/outpath.py` — `build_output_path` mirrors the input structure under the output dir, `filter_out_dir_files` keeps an out-dir nested inside a scanned tree from being re-converted. Both branches in `convert.py` use it; don't reimplement per path.
- **`ffpb.main(argv=...)` prepends `"ffmpeg"` itself** — args exclude the binary name. `_run_ffmpeg` runs `subprocess` directly for the pool and `--quiet` and must add it: `["ffmpeg"] + overwrite_args + _ffmpeg_args(...) + ["-loglevel", "error"]`.
- **Never isolate config in tests via APPDATA-style env vars** — on Windows, platformdirs resolves the real profile through the Win32 shell API and ignores them. The autouse `isolated_config` fixture uses the `CONVOPUS_CONFIG` override, which subprocesses inherit.
- **ffmpeg won't overwrite existing outputs by default** — it prompts `[y/N]` (handled interactively on the sequential path via ffpb). Both paths treat a refusal as a failure: the original is kept and the run exits 1. `-y/--overwrite` passes `-y` (no prompt); `--skip-existing` never reaches ffmpeg for such files.
- **Originals are only deleted after a successful conversion.** `convert_file`/`_convert_file_direct` raise `ConversionError` on a nonzero ffmpeg status, `convert_folder` returns the number of failed files (never aborting the batch), and `main()` exits 1 when anything failed. Add a test for any change to this path: a failed conversion deleting the source is unrecoverable.
- **Output collisions are resolved before any conversion runs.** `plan_conversions` (used by `convert_folder` and by the single-file path in `cli.convert`) skips an output that matches any input in the batch and any output a previous input already claimed, and skips existing outputs only with `--skip-existing`. Never bypass it to add a new input source: the guards are what keep `-c wav` or `a.wav`+`a.flac` from destroying a file.
- **Convertible extensions are matched case-insensitively** (`SONG.FLAC` matches `.flac`), and `--out` filtering uses `os.path.normcase` so Windows path case does not defeat it.
- **`-c/--container` is normalized** (`.ogg`, `ogg` and `.OGG` all work); empty `-c`/`-b` values are rejected by argparse.
- **`-j/--jobs N` implies `-m`** and is rejected together with `-nm`; `-q/--quiet` swaps ffpb for the direct runner and disables the total bar, so ffmpeg errors still reach stderr. `-y/--overwrite` and `--skip-existing` are mutually exclusive; both have `Config` defaults (`overwrite`, `skip_existing`).

## CI / release

- Test workflow on every push/PR: ruff check + format check, ty typecheck, pytest with coverage — matrix {ubuntu, windows} × Python {3.11, 3.14}. Coverage is gated at 80% (`[tool.coverage.report] fail_under`), and `tests/test_ci.py` fails when ffmpeg is missing in CI so integration tests cannot skip silently.
- Publishing to PyPI is automatic when a GitHub Release is published (`python-publish.yml` runs `python -m build` + twine upload). CodeQL scans pushes/PRs to main.
