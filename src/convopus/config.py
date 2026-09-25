"""User configuration: a typed, tolerant, self-healing config file."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from platformdirs import user_config_path

APP_NAME = "convopus"
APP_AUTHOR = "D221"
ENV_OVERRIDE = "CONVOPUS_CONFIG"

_COMMON_TYPES = (
    ".flac",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".webm",
    ".mp4",
    ".avi",
    ".mkv",
    ".mpc",
    ".wma",
)


def _warn(message: str) -> None:
    print(f"convopus: warning: {message}", file=sys.stderr)


def _as_bitrate(value: object, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    _warn(f"bitrate={value!r} is not a string; using default {default!r}")
    return default


def _as_extension(value: object, default: str) -> str:
    if isinstance(value, str) and value.strip():
        extension = value.strip().lower()
        return extension if extension.startswith(".") else f".{extension}"
    _warn(f"container={value!r} is not a string; using default {default!r}")
    return default


def _as_vbr(value: object, default: str) -> str:
    if isinstance(value, str) and value.lower() in ("on", "off"):
        return value.lower()
    _warn(f"vbr={value!r} must be 'on' or 'off'; using default {default!r}")
    return default


def _as_bool(name: str, value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.lower() in (
        "true",
        "false",
        "yes",
        "no",
        "on",
        "off",
    ):
        return value.lower() in ("true", "yes", "on")
    _warn(f"{name}={value!r} is not a boolean; using default {default}")
    return default


def _as_common_types(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        extensions = []
        for item in value:
            if isinstance(item, str) and item.strip():
                extension = item.strip().lower()
                extensions.append(
                    extension if extension.startswith(".") else f".{extension}"
                )
        if extensions:
            return tuple(extensions)
    _warn(f"common_types={value!r} is not a list of extensions; using defaults")
    return default


@dataclass(frozen=True)
class Config:
    """convopus user configuration."""

    bitrate: str = "128k"
    container: str = ".opus"
    keep: bool = True
    vbr: str = "on"
    recursive: bool = False
    multi_threading: bool = True
    common_types: tuple[str, ...] = _COMMON_TYPES

    @classmethod
    def from_mapping(cls, raw: object) -> Config:
        """Build a Config from parsed JSON data.

        Keys are matched case-insensitively (legacy configs used
        UPPERCASE keys). Missing keys fall back to defaults, unknown keys
        are ignored, and invalid values are repaired with a warning.
        """
        base = cls()
        if raw is None:
            return base
        if not isinstance(raw, dict):
            _warn(
                "config root must be a JSON object, got "
                f"{type(raw).__name__}; using defaults"
            )
            return base

        data = {
            key.strip().lower(): value
            for key, value in raw.items()
            if isinstance(key, str)
        }
        common_types = data.pop("common_types", None)
        if common_types is None:
            common_types = data.pop("commontypes", None)

        return cls(
            bitrate=_as_bitrate(data.get("bitrate"), base.bitrate),
            container=_as_extension(data.get("container"), base.container),
            keep=_as_bool("keep", data.get("keep"), base.keep),
            vbr=_as_vbr(data.get("vbr"), base.vbr),
            recursive=_as_bool("recursive", data.get("recursive"), base.recursive),
            multi_threading=_as_bool(
                "multi_threading", data.get("multi_threading"), base.multi_threading
            ),
            common_types=_as_common_types(common_types, base.common_types),
        )


def config_path() -> Path:
    """Location of the config file.

    The CONVOPUS_CONFIG environment variable overrides the default
    platform location (useful for tests and portable installs).
    """
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(override)
    return user_config_path(APP_NAME, APP_AUTHOR) / "config.json"


def legacy_config_path() -> Path:
    """Pre-platformdirs config location (appdirs used the roaming dir)."""
    return user_config_path(APP_NAME, APP_AUTHOR, roaming=True) / "config.json"


def write_default(path: Path | None = None) -> Path:
    """Write a default config file and return its path."""
    file = config_path() if path is None else Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(asdict(Config()), indent=4) + "\n", encoding="utf-8")
    return file


def load(path: Path | None = None) -> Config:
    """Load the user configuration.

    A missing file is created with defaults — or, at the default location
    only, migrated from the legacy appdirs location if one exists. Missing
    keys, unknown keys and invalid values never fail: defaults apply (with
    a warning on stderr) so the CLI always runs.
    """
    file = config_path() if path is None else Path(path)
    if not file.is_file():
        migrated = _migrate_legacy_config(file) if path is None else None
        if migrated is not None:
            return migrated
        write_default(file)
        return Config()
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _warn(f"could not read {file} ({error}); using defaults")
        return Config()
    return Config.from_mapping(raw)


def _migrate_legacy_config(file: Path) -> Config | None:
    """Copy a legacy appdirs config to the new location, if one exists."""
    if os.environ.get(ENV_OVERRIDE):
        return None
    legacy = legacy_config_path()
    if legacy == file or not legacy.is_file():
        return None
    try:
        raw = json.loads(legacy.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    _warn(f"migrating config from {legacy} to {file}")
    config = Config.from_mapping(raw)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(asdict(config), indent=4) + "\n", encoding="utf-8")
    return config


def print_config(path: Path | None = None) -> None:
    """Print the config file location and content, then exit."""
    file = config_path() if path is None else Path(path)
    print(file)
    if file.is_file():
        print(file.read_text(encoding="utf-8"), end="")
    sys.exit()
