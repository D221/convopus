"""End-to-end tests that run real ffmpeg conversions.

Skipped automatically when ffmpeg is not on PATH. The multiprocessing
test deliberately runs the CLI as a subprocess: Windows spawn semantics
inside pytest are a trap, and the subprocess exercises the real
__main__ guard + worker bootstrap path.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

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


def test_multiprocessing_folder_subprocess(tmp_path, make_wav):
    root = tmp_path / "music"
    (root / "sub").mkdir(parents=True)
    make_wav("a.wav", parent=root)
    make_wav("b.wav", parent=root / "sub")
    out = tmp_path / "out"
    config_dir = tmp_path / "cfg"
    repo_root = Path(__file__).resolve().parent.parent

    env = os.environ.copy()
    env["CONVOPUS_TEST_CONFIG_DIR"] = str(config_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent / "_mt_entry.py"),
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
        env=env,
        cwd=repo_root,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (out / "a.opus").is_file()
    assert (out / "sub" / "b.opus").is_file()
    assert (config_dir / "config.json").is_file()
