"""Tests for file collection and output resolution in convert.py."""

import os

from convopus.convert import _collect_files, _resolve_output_file


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
