"""Tests for file collection, output resolution and failure handling."""

import os
import signal
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


def test_convert_file_mt_keeps_source_when_ffmpeg_fails(tmp_path, monkeypatch):
    song = tmp_path / "song.wav"
    song.write_bytes(b"not really audio")
    monkeypatch.setattr(
        "convopus.convert.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )

    from convopus.convert import _convert_file_mt

    with pytest.raises(ConversionError):
        _convert_file_mt(str(song), "96k", ".opus", False, "on", False)

    assert song.exists()


def test_convert_file_mt_deletes_source_after_success(tmp_path, monkeypatch):
    from convopus.convert import _convert_file_mt

    song = tmp_path / "song.wav"
    song.write_bytes(b"audio")
    monkeypatch.setattr(
        "convopus.convert.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    _convert_file_mt(str(song), "96k", ".opus", False, "on", False)

    assert not song.exists()


def test_mt_worker_reports_failure_as_data():
    def boom(_file_name):
        raise ConversionError("ffmpeg said no")

    def ok(_file_name):
        return None

    assert _mt_worker("a.wav", boom) == ("a.wav", "ffmpeg said no")
    assert _mt_worker("b.wav", ok) == ("b.wav", None)


def test_mt_worker_reports_oserror_as_data():
    def boom(_file_name):
        raise OSError("disk went away")

    assert _mt_worker("a.wav", boom) == ("a.wav", "disk went away")


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
    assert "1 file(s) failed" in capsys.readouterr().err


def test_convert_folder_reports_no_files(tmp_path, capsys):
    failures = convert_folder(
        str(tmp_path), "96k", ".opus", True, "on", [".wav"], False, False
    )

    assert failures == 0
    assert "No files to convert" in capsys.readouterr().out


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

    def imap_unordered(self, func, files):
        if self.error is not None:
            raise self.error
        for file_name in files:
            yield file_name, self.results.get(file_name)

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

    failures = convert_mod._convert_all_mt(lambda file_name: None, ["a.wav", "b.wav"])

    assert failures == [("a.wav", "ffmpeg said no")]
    assert pool.closed is True
    assert pool.joined is True
    assert pool.terminated is False


def test_convert_all_mt_terminates_pool_on_interrupt(monkeypatch):
    from convopus import convert as convert_mod

    pool = _FakePool(error=KeyboardInterrupt())
    monkeypatch.setattr(convert_mod, "Pool", lambda size: pool)

    with pytest.raises(KeyboardInterrupt):
        convert_mod._convert_all_mt(lambda file_name: None, ["a.wav"])

    assert pool.terminated is True
    assert pool.joined is True
    assert pool.closed is False


def test_convert_folder_multiprocessing_branch(tmp_path, monkeypatch):
    (tmp_path / "a.wav").write_bytes(b"a")
    seen = {}

    def fake_convert_all(convert_func, files):
        seen["files"] = list(files)
        return []

    monkeypatch.setattr("convopus.convert._convert_all_mt", fake_convert_all)

    failures = convert_folder(
        str(tmp_path), "96k", ".opus", True, "on", [".wav"], False, False, None, True
    )

    assert failures == 0
    assert [os.path.basename(f) for f in seen["files"]] == ["a.wav"]
