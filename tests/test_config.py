"""Tests for config file handling."""

import json
from pathlib import Path

from convopus.config import (
    DEFAULT_CONFIG,
    REQUIRED_KEYS,
    get_config_path,
    read_config,
)


def test_read_config_generates_missing_file():
    assert not Path(get_config_path()).is_file()
    config = read_config()
    assert Path(get_config_path()).is_file()
    assert config["BITRATE"] == "128k"


def test_generated_config_matches_defaults_and_required_keys():
    read_config()
    on_disk = json.loads(Path(get_config_path()).read_text(encoding="utf-8"))
    assert on_disk == DEFAULT_CONFIG
    for key in REQUIRED_KEYS:
        assert key in on_disk


def test_read_config_returns_existing_content(write_config):
    write_config({"BITRATE": "96k", "CONTAINER": ".ogg"})
    config = read_config()
    assert config == {"BITRATE": "96k", "CONTAINER": ".ogg"}
