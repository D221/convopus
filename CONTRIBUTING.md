# Contributing

Thanks for considering a contribution. convopus is small on purpose — a thin, predictable wrapper around `ffmpeg` — so changes that keep it that way are the easiest to accept.

## Setup

You need [uv](https://docs.astral.sh/uv/) and `ffmpeg` on your `PATH` (only the integration tests need ffmpeg; the unit tests do not).

```bash
uv sync
```

## Commands

```bash
uv run convopus <file-or-dir>          # run the CLI
uv run pytest                          # everything (~3 s)
uv run pytest -m "not integration"     # fast unit-only loop
uv run ruff check src/ tests/          # lint
uv run ruff format src/ tests/         # format
uv run ty check src/ tests/            # typecheck
```

No tool has a config file: ruff and ty run on their defaults, so the defaults are the contract. `pytest` config lives in `pyproject.toml`.

## What a change should look like

- **One logical change per pull request.** Dependabot and the test matrix will do the rest.
- **Keep both conversion paths in step.** `convopus/convert.py` has a sequential path (`convert_file`/`convert_folder`) and a multiprocessing one (`_convert_file_mt`). `_ffmpeg_args` builds the argument list for both; if you touch it, both paths must stay behaviour-identical.
- **Config must never break the CLI.** `convopus/config.py` repairs invalid values with a warning instead of raising. New keys belong in the `Config` dataclass with a sane default and a tolerant parser.
- **Add a test.** Unit tests need no ffmpeg; put anything that shells out under the `integration` marker so it is skipped when ffmpeg is missing.
- **Type annotations** are expected on new code; `ty` runs in CI.

## Releasing (maintainers)

1. Bump `__version__` in `src/convopus/__init__.py` — it is the single source of truth (`pyproject.toml` and the CLI read it).
2. Add the release to `CHANGELOG.md`.
3. Tag and push, then publish the GitHub release:

```bash
git tag v1.6.0 && git push --tags
```

Publishing the GitHub release builds the sdist/wheel and uploads to PyPI (trusted publishing), and attaches `convopus-<version>-windows-x64.exe` to the release.

Regenerating the logo or icon (both CC0) is only needed when the mark changes:

```bash
uv run python tools/make_logo.py                                 # docs/logo.svg
uv run --with cairosvg --with pillow python tools/make_icon.py   # docs/icon.ico
```