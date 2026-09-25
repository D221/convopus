"""Helpers for building output paths for the --out option."""

import os


def build_output_path(input_root, input_file, output_dir, file_container, mp3):
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


def filter_out_dir_files(files_to_convert, output_dir):
    """Drop files already inside output_dir from the conversion list.

    Prevents converting freshly created outputs when --out points inside
    a recursively scanned input folder and the container extension is
    itself in COMMONTYPES (e.g. .ogg).
    """
    if not output_dir:
        return files_to_convert
    out_prefix = os.path.abspath(output_dir) + os.sep
    return [
        file_name
        for file_name in files_to_convert
        if not os.path.abspath(file_name).startswith(out_prefix)
    ]
