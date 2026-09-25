"""Tests for --out output path mirroring."""

from convopus.outpath import build_output_path, filter_out_dir_files


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
