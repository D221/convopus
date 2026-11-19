"""Tests for file collection, output resolution and failure handling."""

import os
import signal
import sys
from types import SimpleNamespace

import pytest

from convopus.convert import (
    ConversionError,
    _collect_files,
    _mt_worker,
    _resolve_output_file,
    _signal_handler,
    convert_file,
    convert_folder,
)


def test_collect_recursive_includes_subdirs(tmp_path):
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    (root / "a.wav").touch()
    (sub / "b.wav").touch()
    (sub / "notes.txt").touch()

    files = _collect_files(str(root), [".wav"], True)

    assert sorted(os.path.basename(f) for f in files) == ["a.wav", "b.wav"]


def test_collect_non_recursive_ignores_subdirs(tmp_path):
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    (root / "a.wav").touch()
    (sub / "b.wav").touch()

    files = _collect_files(str(root), [".wav"], False)

    assert [os.path.basename(f) for f in files] == ["a.wav"]


def test_collect_filters_by_common_types(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.flac").touch()
    (root / "b.mp3").touch()
    (root / "c.ogg").touch()
    (root / "d.txt").touch()

    files = _collect_files(str(root), [".flac", ".mp3"], False)

    assert sorted(os.path.basename(f) for f in files) == ["a.flac", "b.mp3"]


def test_collect_is_case_insensitive(tmp_path):
    """`SONG.FLAC` must match the default lowercase `.flac` entry."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "SONG.FLAC").touch()
    (root / "other.WaV").touch()

    files = _collect_files(str(root), [".flac", ".wav"], False)

    assert sorted(os.path.basename(f) for f in files) == ["SONG.FLAC", "other.WaV"]


def test_resolve_defaults_to_in_place(tmp_path):
    song = tmp_path / "song.wav"
    song.touch()
    result = _resolve_output_file(str(song), ".opus", False, None, None)
    assert result == str(tmp_path / "song.opus")


def test_resolve_mp3_in_place(tmp_path):
    song = tmp_path / "song.wav"
    song.touch()
    result = _resolve_output_file(str(song), ".opus", True, None, None)
    assert result == str(tmp_path / "song.mp3")


def test_resolve_mirrors_under_out_dir(tmp_path):
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    out = tmp_path / "out"
    result = _resolve_output_file(
        str(sub / "song.wav"), ".opus", False, str(root), str(out)
    )
    assert result == str(out / "sub" / "song.opus")


def test_convert_file_deletes_source_after_success(tmp_path, monkeypatch):
    song = tmp_path / "song.wav"
    song.write_bytes(b"audio")
    monkeypatch.setattr("convopus.convert.ffpb.main", lambda **kwargs: 0)

    convert_file(str(song), "96k", ".opus", False, "on", False)

    assert not song.exists()


def test_convert_file_keeps_source_when_ffmpeg_fails(tmp_path, monkeypatch):
    """A failed conversion must never delete the original (regression)."""
    song = tmp_path / "song.wav"
    song.write_bytes(b"not really audio")
    monkeypatch.setattr("convopus.convert.ffpb.main", lambda **kwargs: 1)

    with pytest.raises(ConversionError):
        convert_file(str(song), "96k", ".opus", False, "on", False)

    assert song.exists()
    assert not (tmp_path / "song.opus").exists()


def test_convert_file_keeps_source_when_ffmpeg_is_missing(tmp_path, monkeypatch):
    song = tmp_path / "song.wav"
    song.write_bytes(b"audio")

    def missing_ffmpeg(**kwargs):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr("convopus.convert.ffpb.main", missing_ffmpeg)

    with pytest.raises(OSError):
        convert_file(str(song), "96k", ".opus", False, "on", False)

    assert song.exists()


def test_convert_file_direct_keeps_source_when_ffmpeg_fails(tmp_path, monkeypatch):
    song = tmp_path / "song.wav"
    song.write_bytes(b"not really audio")
    monkeypatch.setattr(
        "convopus.convert.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )

    from convopus.convert import _convert_file_direct

    with pytest.raises(ConversionError):
        _convert_file_direct(str(song), "96k", ".opus", False, "on", False)

    assert song.exists()


def test_convert_file_direct_deletes_source_after_success(tmp_path, monkeypatch):
    from convopus.convert import _convert_file_direct

    song = tmp_path / "song.wav"
    song.write_bytes(b"audio")
    monkeypatch.setattr(
        "convopus.convert.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    _convert_file_direct(str(song), "96k", ".opus", False, "on", False)

    assert not song.exists()


def test_mt_worker_reports_failure_as_data():
    def boom(_file_name, **_kwargs):
        raise ConversionError("ffmpeg said no")

    def ok(_file_name, **_kwargs):
        return None

    assert _mt_worker(("a.wav", "a.opus"), boom) == ("a.wav", "ffmpeg said no")
    assert _mt_worker(("b.wav", "b.opus"), ok) == ("b.wav", None)


def test_mt_worker_reports_oserror_as_data():
    def boom(_file_name, **_kwargs):
        raise OSError("disk went away")

    assert _mt_worker(("a.wav", "a.opus"), boom) == ("a.wav", "disk went away")


def test_mt_worker_passes_the_planned_output():
    seen = {}

    def record(file_name, **kwargs):
        seen["file_name"] = file_name
        seen["output_file"] = kwargs["output_file"]

    _mt_worker(("a.wav", "out/a.opus"), record)

    assert seen == {"file_name": "a.wav", "output_file": "out/a.opus"}


def test_convert_folder_continues_after_failure(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.wav").write_bytes(b"a")
    (tmp_path / "b.wav").write_bytes(b"b")
    attempted = []

    def fake_convert(file_name, **kwargs):
        attempted.append(os.path.basename(file_name))
        if file_name.endswith("a.wav"):
            raise ConversionError("ffmpeg exited with status 1")

    monkeypatch.setattr("convopus.convert.convert_file", fake_convert)

    failures = convert_folder(
        str(tmp_path), "96k", ".opus", False, "on", [".wav"], False, False
    )

    assert failures == 1
    assert attempted == ["a.wav", "b.wav"]
    assert "1 file failed to convert" in capsys.readouterr().err


def test_convert_folder_reports_no_files(tmp_path, capsys):
    failures = convert_folder(
        str(tmp_path), "96k", ".opus", True, "on", [".wav"], False, False
    )

    assert failures == 0
    assert "No files to convert" in capsys.readouterr().out


def test_convert_folder_reports_plural_failures(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.wav").write_bytes(b"a")
    (tmp_path / "b.wav").write_bytes(b"b")

    def boom(**kwargs):
        raise ConversionError("ffmpeg said no")

    monkeypatch.setattr("convopus.convert.convert_file", boom)

    failures = convert_folder(
        str(tmp_path), "96k", ".opus", True, "on", [".wav"], False, False
    )

    assert failures == 2
    assert "2 files failed to convert" in capsys.readouterr().err


def test_convert_folder_quiet_uses_direct_runner(tmp_path, monkeypatch):
    (tmp_path / "a.wav").write_bytes(b"a")
    seen = []
    monkeypatch.setattr(
        "convopus.convert.convert_file",
        lambda **kwargs: pytest.fail("ffpb runner used in quiet mode"),
    )
    monkeypatch.setattr(
        "convopus.convert._convert_file_direct",
        lambda **kwargs: seen.append(kwargs["file_name"]),
    )

    failures = convert_folder(
        str(tmp_path),
        "96k",
        ".opus",
        True,
        "on",
        [".wav"],
        False,
        False,
        None,
        False,
        None,
        True,
    )

    assert failures == 0
    assert [os.path.basename(f) for f in seen] == ["a.wav"]


def test_signal_handler_exits_with_128_plus_signal():
    with pytest.raises(SystemExit) as excinfo:
        _signal_handler(signal.SIGINT, None)
    assert excinfo.value.code == 130


class _FakePool:
    """Stand-in for multiprocessing.Pool so the mt branch stays unit-testable."""

    def __init__(self, results=None, error=None):
        self.results = results or {}
        self.error = error
        self.closed = False
        self.joined = False
        self.terminated = False

    def imap_unordered(self, func, items):
        if self.error is not None:
            raise self.error
        for item in items:
            yield item[0], self.results.get(item[0])

    def close(self):
        self.closed = True

    def join(self):
        self.joined = True

    def terminate(self):
        self.terminated = True


def test_convert_all_mt_aggregates_failures(monkeypatch):
    from convopus import convert as convert_mod

    pool = _FakePool({"a.wav": "ffmpeg said no", "b.wav": None})
    monkeypatch.setattr(convert_mod, "Pool", lambda size: pool)

    failures = convert_mod._convert_all_mt(
        lambda file_name: None, [("a.wav", "a.opus"), ("b.wav", "b.opus")]
    )

    assert failures == [("a.wav", "ffmpeg said no")]
    assert pool.closed is True
    assert pool.joined is True
    assert pool.terminated is False


def test_convert_all_mt_terminates_pool_on_interrupt(monkeypatch):
    from convopus import convert as convert_mod

    pool = _FakePool(error=KeyboardInterrupt())
    monkeypatch.setattr(convert_mod, "Pool", lambda size: pool)

    with pytest.raises(KeyboardInterrupt):
        convert_mod._convert_all_mt(lambda file_name: None, [("a.wav", "a.opus")])

    assert pool.terminated is True
    assert pool.joined is True
    assert pool.closed is False


def test_convert_all_mt_uses_requested_jobs(monkeypatch):
    from convopus import convert as convert_mod

    sizes = []
    pool = _FakePool()

    def fake_pool(size):
        sizes.append(size)
        return pool

    monkeypatch.setattr(convert_mod, "Pool", fake_pool)

    convert_mod._convert_all_mt(lambda file_name: None, [("a.wav", "a.opus")], jobs=3)

    assert sizes == [3]


def test_convert_all_mt_defaults_to_cpu_count(monkeypatch):
    from convopus import convert as convert_mod

    sizes = []
    monkeypatch.setattr(
        convert_mod,
        "Pool",
        lambda size: sizes.append(size) or _FakePool(),
    )

    convert_mod._convert_all_mt(lambda file_name: None, [("a.wav", "a.opus")])

    assert sizes == [convert_mod.cpu_count()]


def test_convert_folder_multiprocessing_branch(tmp_path, monkeypatch):
    (tmp_path / "a.wav").write_bytes(b"a")
    seen = {}

    def fake_convert_all(convert_func, items, jobs=None, quiet=False):
        seen["items"] = list(items)
        return []

    monkeypatch.setattr("convopus.convert._convert_all_mt", fake_convert_all)

    failures = convert_folder(
        str(tmp_path), "96k", ".opus", True, "on", [".wav"], False, False, None, True
    )

    assert failures == 0
    assert [os.path.basename(f) for f, _ in seen["items"]] == ["a.wav"]


def test_plan_conversions_is_identity_without_conflicts(tmp_path):
    from convopus.convert import plan_conversions

    song = tmp_path / "song.wav"
    song.write_bytes(b"a")

    conversions, skipped = plan_conversions(
        [str(song)], ".opus", False, str(tmp_path), None, False
    )

    assert conversions == [(str(song), str(tmp_path / "song.opus"))]
    assert skipped == []


def test_plan_conversions_skips_output_equal_to_input(tmp_path):
    """`-c wav` on a wav input must never overwrite the source."""
    from convopus.convert import plan_conversions

    song = tmp_path / "song.wav"
    song.write_bytes(b"a")

    conversions, skipped = plan_conversions(
        [str(song)], ".wav", False, str(tmp_path), None, False
    )

    assert conversions == []
    assert len(skipped) == 1
    assert "would overwrite an input file" in skipped[0][1]


def test_plan_conversions_never_overwrites_another_input(tmp_path):
    """`-c wav` on a.flac + a.wav must not let a.flac replace a.wav."""
    from convopus.convert import plan_conversions

    wav = tmp_path / "a.wav"
    flac = tmp_path / "a.flac"
    wav.write_bytes(b"a")
    flac.write_bytes(b"b")

    conversions, skipped = plan_conversions(
        [str(wav), str(flac)], ".wav", False, str(tmp_path), None, False
    )

    assert conversions == []
    assert len(skipped) == 2
    assert all("would overwrite an input file" in reason for _, reason in skipped)


def test_plan_conversions_skips_existing_outputs_only_when_asked(tmp_path):
    from convopus.convert import plan_conversions

    song = tmp_path / "song.wav"
    song.write_bytes(b"a")
    (tmp_path / "song.opus").write_bytes(b"existing")

    kept, skipped = plan_conversions(
        [str(song)], ".opus", False, str(tmp_path), None, False
    )
    assert len(kept) == 1
    assert skipped == []

    conversions, skipped = plan_conversions(
        [str(song)], ".opus", False, str(tmp_path), None, True
    )
    assert conversions == []
    assert "already exists" in skipped[0][1]


def test_plan_conversions_detects_output_collisions(tmp_path, capsys):
    """`a.wav` and `a.flac` both map to `a.opus`; only one may win."""
    from convopus.convert import plan_conversions, report_skipped

    wav = tmp_path / "a.wav"
    flac = tmp_path / "a.flac"
    wav.write_bytes(b"a")
    flac.write_bytes(b"b")

    conversions, skipped = plan_conversions(
        [str(wav), str(flac)], ".opus", False, str(tmp_path), None, False
    )

    assert len(conversions) == 1
    assert len(skipped) == 1
    assert "another input" in skipped[0][1]

    report_skipped(skipped)
    assert "Skipped 1 file:" in capsys.readouterr().out


@pytest.mark.skipif(
    sys.platform not in ("win32", "darwin"),
    reason="Linux filesystems really do distinguish SONG.WAV from SONG.wav",
)
def test_plan_conversions_compares_paths_case_insensitively(tmp_path):
    """Windows and macOS resolve `SONG.WAV` and `SONG.wav` to one file."""
    from convopus.convert import plan_conversions

    song = tmp_path / "SONG.WAV"
    song.write_bytes(b"a")

    conversions, skipped = plan_conversions(
        [str(song)], ".wav", False, str(tmp_path), None, False
    )

    assert conversions == []
    assert len(skipped) == 1


def test_report_skipped_describes_every_file(capsys):
    from convopus.convert import report_skipped

    report_skipped([("a.wav", "reason one"), ("b.wav", "reason two")])

    out = capsys.readouterr().out
    assert "Skipped 2 files:" in out
    assert "a.wav: reason one" in out
    assert "b.wav: reason two" in out


def test_report_skipped_is_quiet_without_skips(capsys):
    from convopus.convert import report_skipped

    report_skipped([])

    assert capsys.readouterr().out == ""


def test_convert_folder_skip_existing_leaves_outputs_alone(
    tmp_path, monkeypatch, capsys
):
    (tmp_path / "a.wav").write_bytes(b"a")
    existing = tmp_path / "a.opus"
    existing.write_bytes(b"kept")
    monkeypatch.setattr(
        "convopus.convert.convert_file",
        lambda **kwargs: pytest.fail("existing output must not be converted"),
    )

    failures = convert_folder(
        str(tmp_path),
        "96k",
        ".opus",
        True,
        "on",
        [".wav"],
        False,
        False,
        None,
        False,
        None,
        False,
        False,
        True,
    )

    assert failures == 0
    assert existing.read_bytes() == b"kept"
    assert "already exists" in capsys.readouterr().out


def test_convert_folder_overwrite_reaches_ffmpeg(tmp_path, monkeypatch):
    (tmp_path / "a.wav").write_bytes(b"a")
    seen = []

    def fake_convert(file_name, **kwargs):
        seen.append(kwargs["overwrite"])

    monkeypatch.setattr("convopus.convert.convert_file", fake_convert)

    convert_folder(
        str(tmp_path),
        "96k",
        ".opus",
        True,
        "on",
        [".wav"],
        False,
        False,
        None,
        False,
        None,
        False,
        True,
    )

    assert seen == [True]


def test_convert_file_passes_overwrite_flag_to_ffmpeg(tmp_path, monkeypatch):
    song = tmp_path / "song.wav"
    song.write_bytes(b"audio")
    argv = []
    monkeypatch.setattr(
        "convopus.convert.ffpb.main",
        lambda **kwargs: argv.extend(kwargs["argv"]) or 0,
    )

    convert_file(str(song), "96k", ".opus", True, "on", False, overwrite=True)

    assert argv[0] == "-y"


def test_convert_file_direct_passes_overwrite_flag_to_ffmpeg(tmp_path, monkeypatch):
    from convopus.convert import _convert_file_direct

    song = tmp_path / "song.wav"
    song.write_bytes(b"audio")
    commands = []
    monkeypatch.setattr(
        "convopus.convert.subprocess.run",
        lambda command, **kwargs: (
            commands.append(command) or SimpleNamespace(returncode=0)
        ),
    )

    _convert_file_direct(str(song), "96k", ".opus", True, "on", False, overwrite=True)

    assert commands[0][:2] == ["ffmpeg", "-y"]
