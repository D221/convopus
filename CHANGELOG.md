# Changelog

All notable changes to convopus are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `-j/--jobs N` caps the multiprocessing pool (and implies `-m`); `-q/--quiet` disables progress bars for logs and scripts.
- `-y/--overwrite` replaces existing output files without the interactive `[y/N]` prompt; `--skip-existing` leaves already-converted files alone. Both are also available as `overwrite` / `skip_existing` in the config file.
- Output safety guards: a file whose output would equal its own input, and a second input that maps to an output another input already claimed (`a.wav` + `a.flac` -> `a.opus`), are skipped and reported instead of overwriting or double-converting.
- `--version` prints `convopus <version>` instead of the interpreter and script path.
- README troubleshooting table and exit-code reference.

### Fixed

- The failure summary uses correct grammar (`1 file failed`, not `1 file(s) failed`).

## [1.6.1] - 2026-11-19

### Fixed

- `-dk` no longer deletes an original when its conversion fails. Originals are removed only after ffmpeg reports success, on both the sequential and multiprocessing paths.
- A missing or broken ffmpeg now exits with status 1 instead of 0, and a failed run exits 1 as well, so scripts can detect it.
- `-c ogg` (no dot) and `.OGG` (uppercase) now produce `song.ogg` instead of `songogg` / `song.OGG`; empty `-c` and `-b` values are rejected.
- Files with uppercase extensions (`SONG.FLAC`) are converted, and a `--out` directory nested inside the input tree is no longer re-converted when the path differs only in case.
- One failing file no longer aborts a multiprocessing batch: remaining files continue and a summary is printed.

### Changed

- The test suite gates coverage at 80% and uses `--strict-markers`/`--strict-config`; CI installs ffmpeg on Windows and fails if it is missing, so integration tests can no longer skip silently.

## [1.6.0] - 2026-11-17

### Added

- Windows builds in CI: a `convopus.exe` is attached to every GitHub release, with the CC0 app icon.
- Dependabot keeps `uv.lock` and the GitHub Actions current; patch and minor bumps merge themselves once CI is green.
- Logo and icon are generated from a wave equation by `tools/make_logo.py` / `tools/make_icon.py` and dedicated to the public domain under CC0.

### Changed

- Requires **Python 3.11+** — 3.10 reached end of life. Tested on 3.11 and 3.14.
- CI cancels superseded runs, caps every job, and uses least-privilege workflow tokens.
- PyPI releases authenticate with trusted publishing (OIDC) instead of a long-lived API token, and ship build attestations.
- The frozen executable is smaller: OpenSSL and the unused compression modules are no longer bundled (10.3 MB → 6.8 MB).

### Fixed

- The frozen executable hung on folder conversions: the worker processes re-executed the entry point. `multiprocessing.freeze_support()` is now called.
- `build.spec` pointed at a `main.py` that no longer existed, so the documented exe build failed.

## [1.5.0] - 2026-09-26

### Added

- `-o` / `--out` writes converted files under a separate directory, mirroring the input structure.
- Multiple input paths in a single run.
- `python -m convopus` as an alternative entry point.
- A pytest suite: unit tests for ffmpeg arguments, output paths, config and the CLI, plus integration tests that run real ffmpeg conversions.

### Changed

- Packaging moved to `pyproject.toml` with `uv` and a committed `uv.lock`; `setup.py` and `requirements.txt` are gone.
- Configuration is a typed, frozen dataclass built on `platformdirs`, loaded through `CONVOPUS_CONFIG`, and repaired instead of failing: missing or invalid keys fall back to defaults with a warning.
- The legacy `appdirs` roaming location is migrated automatically on first run.
- Config is injected into the CLI rather than read at import time.
- `app.py`/`app_mt.py` merged into `convert.py`; `main.py` and `genconf.py` renamed to `cli.py` and `config.py`.
- CI runs ruff, ty and pytest on Ubuntu and Windows.
- The vendored `ffpb` progress-bar helper is a proper subpackage.

### Fixed

- Progress-bar filenames on paths with mixed separators.

## [1.4.2] - 2024-08-16

### Added

- Experimental MP3 output (`--mp3`): VBR gives V0, CBR gives 320k.

[Unreleased]: https://github.com/D221/convopus/compare/v1.6.1...HEAD
[1.6.1]: https://github.com/D221/convopus/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/D221/convopus/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/D221/convopus/compare/v1.4.2...v1.5.0
[1.4.2]: https://github.com/D221/convopus/releases/tag/v1.4.2