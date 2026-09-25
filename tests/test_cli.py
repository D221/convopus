"""Tests for argument parsing and config loading in cli.py."""

import json
from pathlib import Path

import pytest

from convopus.cli import load_config, parse_arguments
from convopus.config import DEFAULT_CONFIG, get_config_path


def test_defaults_come_from_config(make_config):
    config = make_config(BITRATE="96k", CONTAINER=".ogg", VBR="off", RECURSIVE=True)
    args = parse_arguments(["music/"], config)
    assert args.bitrate == "96k"
    assert args.container == ".ogg"
    assert args.vbr == "off"
    assert args.recursive is True


def test_flag_overrides_config_default(make_config):
    args = parse_arguments(["-r", "music/"], make_config(RECURSIVE=False))
    assert args.recursive is True


def test_out_defaults_to_none(make_config):
    args = parse_arguments(["music/"], make_config())
    assert args.out is None


def test_multiple_inputs(make_config):
    args = parse_arguments(["a.wav", "b", "c/"], make_config())
    assert args.input == ["a.wav", "b", "c/"]


def test_keep_flags_mutually_exclusive(make_config):
    with pytest.raises(SystemExit):
        parse_arguments(["-k", "-dk", "music/"], make_config())


def test_mt_flags_mutually_exclusive(make_config):
    with pytest.raises(SystemExit):
        parse_arguments(["-m", "-nm", "music/"], make_config())


def test_version_exits_with_version_string(capsys, make_config):
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-v"], make_config())
    assert excinfo.value.code == 0
    assert "1.4.3" in capsys.readouterr().out


def test_print_config_prints_location_and_exits(capsys, make_config, write_config):
    write_config(make_config())
    with pytest.raises(SystemExit):
        parse_arguments(["--config"], make_config())
    assert "config.json" in capsys.readouterr().out


def test_load_config_generates_and_returns_defaults():
    config = load_config()
    assert config["BITRATE"] == DEFAULT_CONFIG["BITRATE"]
    assert Path(get_config_path()).is_file()


def test_load_config_regenerates_when_keys_missing(monkeypatch, make_config):
    path = Path(get_config_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"BITRATE": "128k"}), encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    with pytest.raises(SystemExit):
        load_config()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == DEFAULT_CONFIG


def test_load_config_exits_when_regeneration_declined(monkeypatch, make_config):
    path = Path(get_config_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"BITRATE": "128k"}), encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    with pytest.raises(SystemExit):
        load_config()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == {"BITRATE": "128k"}


def test_import_does_not_create_config(monkeypatch, tmp_path):
    """Importing the CLI must stay side-effect-free (regression guard)."""
    import subprocess
    import sys

    env_tmp = tmp_path / "fresh-profile"
    env_tmp.mkdir()
    script = (
        "import convopus.config as c\n"
        f"c.user_config_dir = lambda a, b: r'{env_tmp}'\n"
        "import convopus.cli\n"
        "import os\n"
        "raise SystemExit(0 if os.path.isfile(c.get_config_path()) else 1)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
