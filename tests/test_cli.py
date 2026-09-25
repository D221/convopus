"""Tests for argument parsing in cli.py."""

import subprocess
import sys

import pytest

from convopus.cli import parse_arguments
from convopus.config import Config


def test_defaults_come_from_config():
    config = Config(bitrate="96k", container=".ogg", vbr="off", recursive=True)
    args = parse_arguments(["music/"], config)
    assert args.bitrate == "96k"
    assert args.container == ".ogg"
    assert args.vbr == "off"
    assert args.recursive is True


def test_flag_overrides_config_default():
    args = parse_arguments(["-r", "music/"], Config(recursive=False))
    assert args.recursive is True


def test_out_defaults_to_none():
    args = parse_arguments(["music/"], Config())
    assert args.out is None


def test_multiple_inputs():
    args = parse_arguments(["a.wav", "b", "c/"], Config())
    assert args.input == ["a.wav", "b", "c/"]


def test_keep_flags_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_arguments(["-k", "-dk", "music/"], Config())


def test_mt_flags_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_arguments(["-m", "-nm", "music/"], Config())


def test_version_exits_with_version_string(capsys):
    from convopus import __version__

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-v"], Config())
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_print_config_prints_location_and_exits(capsys, isolated_config):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        parse_arguments(["--config"], Config())
    assert "config.json" in capsys.readouterr().out


def test_import_does_not_create_config(isolated_config):
    """Importing the CLI must stay side-effect-free (regression guard)."""
    script = (
        "import os\n"
        "import convopus\n"
        "import convopus.cli\n"
        "from convopus.config import config_path\n"
        "expected = os.environ['CONVOPUS_CONFIG']\n"
        "actual = str(config_path())\n"
        "from_src = os.sep + 'src' + os.sep in convopus.__file__\n"
        "clean = not os.path.isfile(actual)\n"
        "print('module:', convopus.__file__)\n"
        "print('from_src:', from_src)\n"
        "print('path:', actual)\n"
        "print('exists:', os.path.isfile(actual))\n"
        "raise SystemExit(0 if from_src and clean and actual == expected else 1)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r} stdout={result.stdout!r}"
