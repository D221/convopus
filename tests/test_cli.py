"""Tests for argument parsing and the CLI orchestration layer."""

import json
import subprocess
import sys

import pytest

from convopus.cli import convert, parse_arguments
from convopus.config import Config
from convopus.convert import ConversionError


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


def test_container_without_dot_is_normalized():
    """`-c ogg` used to produce files named `songogg`."""
    args = parse_arguments(["-c", "ogg", "music/"], Config())
    assert args.container == ".ogg"


def test_container_is_lowercased_and_dotted():
    args = parse_arguments(["-c", ".OGG", "music/"], Config())
    assert args.container == ".ogg"


def test_empty_container_is_rejected():
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-c", "", "music/"], Config())
    assert excinfo.value.code == 2


def test_empty_bitrate_is_rejected():
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-b", "  ", "music/"], Config())
    assert excinfo.value.code == 2


def test_version_exits_with_version_string(capsys):
    from convopus import __version__

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-v"], Config())
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_version_prints_short_program_name(capsys):
    from convopus import __version__

    with pytest.raises(SystemExit):
        parse_arguments(["-v"], Config())
    assert capsys.readouterr().out.strip() == f"convopus {__version__}"


def test_jobs_is_parsed():
    args = parse_arguments(["-j", "4", "music/"], Config())
    assert args.jobs == 4


@pytest.mark.parametrize("value", ["0", "-1", "many"])
def test_jobs_must_be_a_positive_integer(value):
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-j", value, "music/"], Config())
    assert excinfo.value.code == 2


def test_jobs_conflicts_with_no_multithreading():
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-nm", "-j", "2", "music/"], Config())
    assert excinfo.value.code == 2


def test_quiet_is_parsed():
    assert parse_arguments(["-q", "music/"], Config()).quiet is True


def test_overwrite_flag_is_parsed():
    assert parse_arguments(["-y", "music/"], Config()).overwrite is True


def test_skip_existing_flag_is_parsed():
    args = parse_arguments(["--skip-existing", "music/"], Config())
    assert args.skip_existing is True


def test_overwrite_and_skip_existing_are_mutually_exclusive():
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["-y", "--skip-existing", "music/"], Config())
    assert excinfo.value.code == 2


def test_existing_file_policy_defaults_come_from_config():
    args = parse_arguments(["music/"], Config(skip_existing=True))
    assert args.overwrite is False
    assert args.skip_existing is True


def test_overwrite_flag_overrides_config_skip_existing():
    args = parse_arguments(["-y", "music/"], Config(skip_existing=True))
    assert args.overwrite is True
    assert args.skip_existing is False


def test_skip_existing_flag_overrides_config_overwrite():
    args = parse_arguments(["--skip-existing", "music/"], Config(overwrite=True))
    assert args.overwrite is False
    assert args.skip_existing is True


def test_print_config_prints_location_and_content(capsys, isolated_config):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(json.dumps({"bitrate": "96k"}), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["--config"], Config())
    out = capsys.readouterr().out
    assert excinfo.value.code is None
    assert str(isolated_config) in out
    assert "96k" in out


def test_import_does_not_create_config(isolated_config):
    """Importing the CLI must stay side-effect-free (regression guard)."""
    script = (
        "import os\n"
        "import convopus\n"
        "import convopus.cli\n"
        "from convopus.config import config_path\n"
        "expected = os.environ['CONVOPUS_CONFIG']\n"
        "actual = str(config_path())\n"
        "clean = not os.path.isfile(actual)\n"
        "print('module:', convopus.__file__)\n"
        "print('path:', actual)\n"
        "print('exists:', os.path.isfile(actual))\n"
        "raise SystemExit(0 if clean and actual == expected else 1)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r} stdout={result.stdout!r}"


def test_check_ffmpeg_passes_when_ffmpeg_works(monkeypatch):
    from convopus import cli

    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: None)
    cli.check_ffmpeg()


def test_check_ffmpeg_exits_one_when_missing(monkeypatch, capsys):
    from convopus import cli

    def boom(*args, **kwargs):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(cli.subprocess, "run", boom)
    with pytest.raises(SystemExit) as excinfo:
        cli.check_ffmpeg()
    assert excinfo.value.code == 1
    assert "ffmpeg is not installed" in capsys.readouterr().err


def test_check_ffmpeg_exits_one_when_broken(monkeypatch):
    from convopus import cli

    def broken(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "ffmpeg")

    monkeypatch.setattr(cli.subprocess, "run", broken)
    with pytest.raises(SystemExit) as excinfo:
        cli.check_ffmpeg()
    assert excinfo.value.code == 1


def _run_main(monkeypatch, argv, config, result=0):
    """Run main() with ffmpeg and conversion faked; return convert() args."""
    from convopus import cli

    recorded = {}

    def fake_convert(*args):
        recorded["args"] = args
        return result

    monkeypatch.setattr(cli, "load", lambda: config)
    monkeypatch.setattr(cli, "check_ffmpeg", lambda: None)
    monkeypatch.setattr(cli, "convert", fake_convert)
    monkeypatch.setattr(sys, "argv", ["convopus", *argv])
    cli.main()
    return recorded["args"]


def test_main_uses_config_defaults(monkeypatch):
    args = _run_main(
        monkeypatch,
        ["song.wav"],
        Config(bitrate="96k", container=".ogg", keep=False, multi_threading=False),
    )
    assert args[1] == "96k"
    assert args[2] == ".ogg"
    assert args[3] is False  # keep_files
    assert args[7] is False  # multi_threading


def test_main_keep_flag_overrides_config(monkeypatch):
    args = _run_main(monkeypatch, ["-k", "song.wav"], Config(keep=False))
    assert args[3] is True


def test_main_delete_flag_overrides_config(monkeypatch):
    args = _run_main(monkeypatch, ["-dk", "song.wav"], Config(keep=True))
    assert args[3] is False


def test_main_multithreading_flag_overrides_config(monkeypatch):
    args = _run_main(monkeypatch, ["-m", "song.wav"], Config(multi_threading=False))
    assert args[7] is True


def test_main_no_multithreading_flag_overrides_config(monkeypatch):
    args = _run_main(monkeypatch, ["-nm", "song.wav"], Config(multi_threading=True))
    assert args[7] is False


def test_main_jobs_implies_multithreading(monkeypatch):
    args = _run_main(
        monkeypatch, ["-j", "3", "song.wav"], Config(multi_threading=False)
    )
    assert args[7] is True
    assert args[10] == 3


def test_main_passes_quiet(monkeypatch):
    args = _run_main(monkeypatch, ["-q", "song.wav"], Config())
    assert args[11] is True


def test_main_passes_overwrite(monkeypatch):
    args = _run_main(monkeypatch, ["-y", "song.wav"], Config())
    assert args[12] is True


def test_main_passes_skip_existing(monkeypatch):
    args = _run_main(monkeypatch, ["--skip-existing", "song.wav"], Config())
    assert args[13] is True


def test_main_without_input_prints_usage_hint(monkeypatch, capsys):
    from convopus import cli

    monkeypatch.setattr(cli, "load", lambda: Config())
    monkeypatch.setattr(cli, "check_ffmpeg", lambda: None)
    monkeypatch.setattr(cli, "convert", lambda *args: pytest.fail("should not run"))
    monkeypatch.setattr(sys, "argv", ["convopus"])
    cli.main()
    assert "convopus --help" in capsys.readouterr().out


def test_main_exits_one_when_conversions_fail(monkeypatch):
    with pytest.raises(SystemExit) as excinfo:
        _run_main(monkeypatch, ["song.wav"], Config(), result=2)
    assert excinfo.value.code == 1


def test_main_exits_zero_when_conversions_succeed(monkeypatch):
    _run_main(monkeypatch, ["song.wav"], Config(), result=0)


def test_convert_dispatches_files_and_folders(tmp_path, monkeypatch):
    from convopus import cli

    folder = tmp_path / "music"
    folder.mkdir()
    song = tmp_path / "song.wav"
    song.touch()
    calls = []
    monkeypatch.setattr(
        cli, "convert_folder", lambda *args: calls.append(("folder", args)) or 0
    )
    monkeypatch.setattr(
        cli, "convert_file", lambda *args, **kwargs: calls.append(("file", args))
    )

    failures = convert(
        [str(folder), str(song)],
        "96k",
        ".opus",
        True,
        "on",
        [".wav"],
        False,
        False,
        False,
        None,
    )

    assert failures == 0
    assert [kind for kind, _ in calls] == ["folder", "file"]


def test_convert_counts_invalid_paths(capsys):
    failures = convert(
        ["missing.wav"], "96k", ".opus", True, "on", [".wav"], False, False, False, None
    )
    assert failures == 1
    assert "invalid" in capsys.readouterr().err


def test_convert_counts_conversion_errors(tmp_path, monkeypatch):
    from convopus import cli

    song = tmp_path / "song.wav"
    song.touch()

    def boom(*args, **kwargs):
        raise ConversionError("ffmpeg exited with status 1")

    monkeypatch.setattr(cli, "convert_file", boom)
    failures = convert(
        [str(song)], "96k", ".opus", False, "on", [".wav"], False, False, False, None
    )
    assert failures == 1


def test_convert_single_file_uses_planned_output(tmp_path, monkeypatch):
    from convopus import cli

    song = tmp_path / "song.wav"
    song.touch()
    seen = {}

    def fake_convert(file_name, *args, **kwargs):
        seen["file_name"] = file_name
        seen["output_file"] = kwargs["output_file"]
        seen["overwrite"] = kwargs["overwrite"]

    monkeypatch.setattr(cli, "convert_file", fake_convert)

    failures = convert(
        [str(song)],
        "96k",
        ".opus",
        True,
        "on",
        [".wav"],
        False,
        False,
        False,
        None,
        None,
        False,
        True,
    )

    assert failures == 0
    assert seen == {
        "file_name": str(song),
        "output_file": str(tmp_path / "song.opus"),
        "overwrite": True,
    }


def test_convert_single_file_skip_existing(tmp_path, monkeypatch, capsys):
    from convopus import cli

    song = tmp_path / "song.wav"
    song.touch()
    (tmp_path / "song.opus").touch()
    monkeypatch.setattr(cli, "convert_file", lambda *a, **k: pytest.fail("converted"))

    failures = convert(
        [str(song)],
        "96k",
        ".opus",
        True,
        "on",
        [".wav"],
        False,
        False,
        False,
        None,
        None,
        False,
        False,
        True,
    )

    assert failures == 0
    assert "already exists" in capsys.readouterr().out
