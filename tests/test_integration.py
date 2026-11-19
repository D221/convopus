"""End-to-end tests that run real ffmpeg conversions.

Skipped automatically when ffmpeg is not on PATH. The multiprocessing
test deliberately runs the CLI as a subprocess: Windows spawn semantics
inside pytest are a trap, and the subprocess exercises the real
__main__ guard + worker bootstrap path.
"""

import shutil
import subprocess
import sys

import pytest

from convopus.convert import convert_file, convert_folder

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        shutil.which("ffmpeg") is None, reason="ffmpeg is not available"
    ),
]


def test_convert_folder_sequential_in_place(tmp_path, make_wav):
    root = tmp_path / "music"
    (root / "sub").mkdir(parents=True)
    make_wav("a.wav", parent=root)
    make_wav("b.wav", parent=root / "sub")

    convert_folder(str(root), "96k", ".opus", True, "on", [".wav"], True, False)

    assert (root / "a.opus").is_file()
    assert (root / "sub" / "b.opus").is_file()
    assert (root / "a.wav").is_file()


def test_convert_folder_mirrors_into_out_dir(tmp_path, make_wav):
    root = tmp_path / "music"
    (root / "sub").mkdir(parents=True)
    make_wav("a.wav", parent=root)
    make_wav("b.wav", parent=root / "sub")
    out = tmp_path / "out"

    convert_folder(
        str(root), "96k", ".opus", True, "on", [".wav"], True, False, str(out)
    )

    assert (out / "a.opus").is_file()
    assert (out / "sub" / "b.opus").is_file()
    assert (root / "a.wav").is_file()


def test_convert_folder_flat_out_without_recursive(tmp_path, make_wav):
    sub = tmp_path / "music" / "sub"
    sub.mkdir(parents=True)
    make_wav("b.wav", parent=sub)
    out = tmp_path / "out"

    convert_folder(
        str(sub), "96k", ".opus", True, "on", [".wav"], False, False, str(out)
    )

    assert (out / "b.opus").is_file()


def test_convert_file_mp3(tmp_path, make_wav):
    song = make_wav("song.wav")

    convert_file(str(song), "128k", ".opus", True, "off", True)

    assert (tmp_path / "song.mp3").is_file()


def test_delete_original_when_not_keep(tmp_path, make_wav):
    song = make_wav("gone.wav")

    convert_file(str(song), "96k", ".opus", False, "on", False)

    assert not song.exists()
    assert (tmp_path / "gone.opus").is_file()


def test_multiprocessing_folder_subprocess(tmp_path, make_wav, isolated_config):
    root = tmp_path / "music"
    (root / "sub").mkdir(parents=True)
    make_wav("a.wav", parent=root)
    make_wav("b.wav", parent=root / "sub")
    out = tmp_path / "out"

    # isolated_config points CONVOPUS_CONFIG into tmp_path; the subprocess
    # inherits it, so config.json is generated inside tmp and nowhere else.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "convopus",
            "-k",
            "-m",
            "-r",
            "-b",
            "96k",
            "--out",
            str(out),
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (out / "a.opus").is_file()
    assert (out / "sub" / "b.opus").is_file()
    assert isolated_config.is_file()


def test_failed_conversion_keeps_original(tmp_path):
    """Corrupt input with delete-enabled must not destroy the source."""
    bad = tmp_path / "corrupt.wav"
    bad.write_bytes(b"not a wav at all")

    failures = convert_folder(
        str(tmp_path), "96k", ".opus", False, "on", [".wav"], False, False
    )

    assert failures == 1
    assert bad.exists()
    assert not (tmp_path / "corrupt.opus").exists()


def test_cli_exits_nonzero_and_continues_after_failure(tmp_path, make_wav):
    (tmp_path / "corrupt.wav").write_bytes(b"not a wav at all")
    make_wav("good.wav", parent=tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "convopus", "-nm", "-k", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 1, result.stderr
    assert (tmp_path / "corrupt.wav").is_file()
    assert (tmp_path / "good.opus").is_file()
    assert "1 file failed to convert" in result.stderr


def test_cli_multiprocessing_keeps_failing_original(tmp_path, make_wav):
    """The pool must report a failure without deleting that original."""
    (tmp_path / "corrupt.wav").write_bytes(b"not a wav at all")
    make_wav("good.wav", parent=tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "convopus", "-m", "-dk", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 1, result.stderr
    assert (tmp_path / "corrupt.wav").is_file()
    assert (tmp_path / "good.opus").is_file()
    assert not (tmp_path / "good.wav").exists()


def test_out_dir_nested_in_input_is_not_reconverted(tmp_path, make_wav):
    """Outputs already inside a recursively scanned --out tree are skipped."""
    root = tmp_path / "music"
    (root / "sub").mkdir(parents=True)
    make_wav("a.wav", parent=root)
    make_wav("b.wav", parent=root / "sub")
    out = root / "converted"
    out.mkdir()
    stale_output = out / "stale.ogg"
    stale_output.write_bytes(b"not audio")

    failures = convert_folder(
        str(root),
        "96k",
        ".ogg",
        True,
        "on",
        [".wav", ".ogg"],
        True,
        False,
        str(out),
    )

    assert failures == 0
    assert (out / "a.ogg").is_file()
    assert (out / "sub" / "b.ogg").is_file()
    assert stale_output.is_file()
    assert not (out / "converted").exists()


def _probe_codec(path):
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        pytest.skip("ffprobe is not available")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_opus_output_really_is_opus(tmp_path, make_wav):
    song = make_wav("song.wav")

    convert_file(str(song), "96k", ".opus", True, "on", False)

    assert _probe_codec(tmp_path / "song.opus") == "opus"


def test_mp3_output_really_is_mp3(tmp_path, make_wav):
    song = make_wav("song.wav")

    convert_file(str(song), "128k", ".opus", True, "off", True)

    assert _probe_codec(tmp_path / "song.mp3") == "mp3"
