# AGENTS.md

convopus — small Python CLI (src layout, stdlib + appdirs/tqdm) that converts audio files/directories to Opus (or MP3) by shelling out to ffmpeg. ffmpeg must be on PATH; it is checked at startup and the program exits if missing.

## Commands

```bash
# Setup — src layout: the CLI only works when installed
pip install -e .

# Run (console script defined in setup.cfg)
convopus <file-or-dir>
python -m convopus <file-or-dir>   # also works (__main__.py)

# Manual verification (no test suite exists; .pytest_cache/ is a stale artifact).
# -k keeps originals, -nm avoids the multiprocessing path.
convopus -k -nm -b 96k <some .flac/.wav file>

# Lint, format, typecheck (no config files — tool defaults are the contract).
# CI pylint runs with --exit-zero (never blocks); ruff + ty are the real local gates.
uvx ruff check src/
uvx ruff format src/
uvx ty check src/

# Windows exe build (spec file is intentionally not gitignored)
pyinstaller build.spec   # -> dist/convopus.exe
```

## Gotchas

- **Config is read at import time** (`CONFIG_DATA = read_config()` at module level in `main.py`) from the OS user-config dir (`%LocalAppData%\D221\convopus\config.json` on Windows). There is no config file in this repo. Required keys: `BITRATE`, `CONTAINER`, `VBR`, `RECURSIVE`, `COMMONTYPES`; `KEEP` and `MULTI_THREADING` are optional. A missing key (e.g. older user configs without `RECURSIVE`) triggers an interactive "generate new config?" prompt and exit. Importing `convopus` anywhere (scripts, tests) triggers this read.
- **Version single source of truth**: `__version__` literal in `src/convopus/__init__.py`; `setup.cfg` picks it up via `attr: convopus.__version__` and `main.py` imports it for `--version`. Don't hardcode versions anywhere else.
- **ffmpeg args are built twice** and must stay in sync: `app.py::convert_file` (single-thread path, runs through vendored `ffpb_convopus/ffpb.py`) and `app_mt.py::convert_file_mt` (multiprocessing `Pool` path, direct `subprocess.run`).
- **`ffpb.main(argv=...)` prepends `"ffmpeg"` itself** — pass args without the binary name (as `app.py` does). `app_mt.py` calls subprocess directly and includes it.

## CI / release

- pylint on every push (matrix 3.8/3.9/3.10, `--exit-zero`), CodeQL on pushes/PRs to main.
- Publishing to PyPI is automatic when a GitHub Release is published (`python-publish.yml` runs `python -m build` + twine upload).
