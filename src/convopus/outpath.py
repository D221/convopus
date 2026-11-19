"""Helpers for building output paths for the --out option."""

import os
import sys


def path_key(path: str) -> str:
    """Normalize a path for same-file comparisons.

    `normcase` covers Windows (case-insensitive, backslash separators), but
    it is a no-op on macOS even though the default filesystem there is also
    case-insensitive. Fold case explicitly on macOS so `SONG.WAV` and
    `SONG.wav` are never treated as different files; on the rare
    case-sensitive APFS volume this only makes the guards more cautious.
    """
    key = os.path.normcase(os.path.abspath(path))
    if sys.platform == "darwin":
        key = key.casefold()
    return key


def build_output_path(
    input_root: str,
    input_file: str,
    output_dir: str,
    file_container: str,
    mp3: bool,
) -> str:
    """Build the output path for input_file under output_dir.

    The part of input_file below input_root is mirrored under output_dir,
    so subfolders are recreated when scanning recursively (and, for a flat
    scan or a single file, the file is placed directly in output_dir).
    Parent directories are created as a side effect.
    """
    relative = os.path.relpath(input_file, input_root)
    base, _ = os.path.splitext(relative)
    extension = ".mp3" if mp3 else file_container
    output_file = os.path.join(output_dir, base + extension)
    parent = os.path.dirname(output_file)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return output_file


def filter_out_dir_files(
    files_to_convert: list[str], output_dir: str | None
) -> list[str]:
    """Drop files already inside output_dir from the conversion list.

    Prevents converting freshly created outputs when --out points inside
    a recursively scanned input folder and the container extension is
    itself in COMMONTYPES (e.g. .ogg).
    """
    if not output_dir:
        return files_to_convert
    # path_key matches how the filesystem resolves paths: Windows and macOS
    # are case-insensitive, and Windows uses "\\" as the separator.
    out_prefix = path_key(output_dir) + os.sep
    return [
        file_name
        for file_name in files_to_convert
        if not path_key(file_name).startswith(out_prefix)
    ]
