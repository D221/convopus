"""Tests for --out output path mirroring."""

import os

import pytest

from convopus import outpath
from convopus.outpath import build_output_path, filter_out_dir_files, path_key


def test_mirrors_subdirectory_structure(tmp_path):
    music = tmp_path / "music"
    out = tmp_path / "out"
    input_file = music / "rock" / "song.flac"
    input_file.parent.mkdir(parents=True)

    result = build_output_path(str(music), str(input_file), str(out), ".opus", False)

    assert result == str(out / "rock" / "song.opus")
    assert (out / "rock").is_dir()


def test_flat_for_file_directly_under_input_root(tmp_path):
    music = tmp_path / "music"
    music.mkdir()
    result = build_output_path(
        str(music), str(music / "song.wav"), str(tmp_path / "out"), ".opus", False
    )
    assert result == str(tmp_path / "out" / "song.opus")


def test_mp3_extension_override(tmp_path):
    music = tmp_path / "music"
    music.mkdir()
    result = build_output_path(
        str(music), str(music / "song.wav"), str(tmp_path / "out"), ".opus", True
    )
    assert result == str(tmp_path / "out" / "song.mp3")


def test_custom_container_extension(tmp_path):
    music = tmp_path / "music"
    music.mkdir()
    result = build_output_path(
        str(music), str(music / "song.wav"), str(tmp_path / "out"), ".oga", False
    )
    assert result == str(tmp_path / "out" / "song.oga")


def test_creates_missing_output_directory(tmp_path):
    music = tmp_path / "music"
    music.mkdir()
    out = tmp_path / "nested" / "out"
    assert not out.exists()
    build_output_path(str(music), str(music / "song.wav"), str(out), ".opus", False)
    assert out.is_dir()


def test_filter_removes_files_inside_out_dir(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    inside = out / "song.opus"
    inside.touch()
    outside = tmp_path / "song.wav"
    outside.touch()
    result = filter_out_dir_files([str(inside), str(outside)], str(out))
    assert result == [str(outside)]


def test_filter_keeps_sibling_directory(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    out2 = tmp_path / "out2"
    out2.mkdir()
    sibling = out2 / "song.opus"
    sibling.touch()
    assert filter_out_dir_files([str(sibling)], str(out)) == [str(sibling)]


def test_filter_passthrough_when_no_out_dir():
    files = ["a.wav", "b.wav"]
    assert filter_out_dir_files(files, None) is files


@pytest.mark.skipif(os.name != "nt", reason="case-insensitive filesystems only")
def test_filter_is_case_insensitive_on_windows(tmp_path):
    """Windows resolves `OUT\\song.opus` and `Out\\song.opus` to one file."""
    out = tmp_path / "Out"
    out.mkdir()
    weird = os.path.join(str(out).upper(), "song.opus")

    assert filter_out_dir_files([weird], str(out)) == []


@pytest.mark.skipif(os.name == "nt", reason="normcase already folds case here")
def test_path_key_folds_case_on_macos(tmp_path, monkeypatch):
    """Default macOS filesystems are case-insensitive, unlike normcase."""
    monkeypatch.setattr(outpath.sys, "platform", "darwin")

    assert path_key(str(tmp_path / "Song.WAV")) == path_key(str(tmp_path / "song.wav"))


@pytest.mark.skipif(os.name == "nt", reason="normcase already folds case here")
def test_filter_is_case_insensitive_on_macos(tmp_path, monkeypatch):
    monkeypatch.setattr(outpath.sys, "platform", "darwin")
    out = tmp_path / "Out"
    out.mkdir()
    weird = os.path.join(str(out).upper(), "song.opus")

    assert filter_out_dir_files([weird], str(out)) == []


def test_filter_drops_nested_subdirectories(tmp_path):
    out = tmp_path / "out"
    nested = out / "sub"
    nested.mkdir(parents=True)
    inside = nested / "song.opus"
    inside.touch()

    assert filter_out_dir_files([str(inside)], str(out)) == []
