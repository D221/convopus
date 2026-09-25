"""Audio conversion: sequential and multiprocessing paths."""

import os
import signal
import subprocess
import sys
from functools import partial
from multiprocessing import Pool, cpu_count

from tqdm import tqdm

from convopus.outpath import build_output_path, filter_out_dir_files
from ffpb_convopus import ffpb


def _signal_handler(sig, frame):
    """SIGINT handler."""
    sys.exit(0)


def _collect_files(input_path, config_common_types, recursive):
    """List convertible audio files in or below input_path."""
    if recursive:
        return [
            os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(input_path)
            for filename in filenames
            if filename.endswith(tuple(config_common_types))
        ]
    return [
        os.path.join(input_path, filename)
        for filename in os.listdir(input_path)
        if filename.endswith(tuple(config_common_types))
    ]


def _total_progress_bar(total):
    """Create the shared total progress bar."""
    return tqdm(
        total=total,
        desc="Total:",
        dynamic_ncols=True,
        ncols=0,
        colour="green",
        bar_format="{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]",
    )


def _resolve_output_file(file_name, file_container, mp3, input_root, output_dir):
    """Output next to the input, or mirrored under output_dir when given."""
    if output_dir:
        return build_output_path(
            input_root or ".", file_name, output_dir, file_container, mp3
        )
    if mp3:
        return os.path.splitext(file_name)[0] + ".mp3"
    return os.path.splitext(file_name)[0] + file_container


def _ffmpeg_args(file_name, output_file, prefered_bitrate, vbr, mp3):
    """Shared ffmpeg argument list (without the binary name)."""
    args = [
        "-i",
        file_name,
        "-vn",
        "-c:a",
        "libmp3lame" if mp3 else "libopus",
        "-q:a" if (mp3 and vbr == "on") else None,
        "0" if (mp3 and vbr == "on") else None,  # VBR for MP3
        "-b:a" if (mp3 and vbr == "off") or not mp3 else None,
        "320k" if (mp3 and vbr == "off") else prefered_bitrate if not mp3 else None,
        "-vbr" if not mp3 else None,
        vbr if not mp3 else None,  # VBR for Opus
        output_file,
    ]
    return [arg for arg in args if arg is not None]


def convert_file(
    file_name,
    prefered_bitrate,
    file_container,
    keep_files,
    vbr,
    mp3,
    input_root=None,
    output_dir=None,
):
    """For converting a single audio file (sequential, with ffpb progress)."""
    output_file = _resolve_output_file(
        file_name, file_container, mp3, input_root, output_dir
    )
    ffpb.main(argv=_ffmpeg_args(file_name, output_file, prefered_bitrate, vbr, mp3))

    if not keep_files:
        os.remove(file_name)


def _convert_file_mt(
    file_name,
    prefered_bitrate,
    file_container,
    keep_files,
    vbr,
    mp3,
    input_root=None,
    output_dir=None,
):
    """For converting a single audio file in a worker process."""
    output_file = _resolve_output_file(
        file_name, file_container, mp3, input_root, output_dir
    )
    ffmpeg_cmd = (
        ["ffmpeg"]
        + _ffmpeg_args(file_name, output_file, prefered_bitrate, vbr, mp3)
        + ["-loglevel", "error"]
    )
    subprocess.run(ffmpeg_cmd, check=True)
    if not keep_files:
        os.remove(file_name)


def convert_folder(
    input_path,
    prefered_bitrate,
    file_container,
    keep_files,
    vbr,
    config_common_types,
    recursive,
    mp3,
    output_dir=None,
    multi_threading=False,
):
    """For converting audio files in a folder."""
    files_to_convert = filter_out_dir_files(
        _collect_files(input_path, config_common_types, recursive), output_dir
    )

    if not files_to_convert:
        print("No files to convert")
        return

    if multi_threading:
        convert_func = partial(
            _convert_file_mt,
            prefered_bitrate=prefered_bitrate,
            file_container=file_container,
            keep_files=keep_files,
            vbr=vbr,
            mp3=mp3,
            input_root=input_path,
            output_dir=output_dir,
        )
        pool = Pool(cpu_count())
        with _total_progress_bar(len(files_to_convert)) as pbar:
            for _ in pool.imap_unordered(convert_func, sorted(files_to_convert)):
                pbar.update(1)
        pool.close()
        # implement KeyboardInterrupt
        return

    signal.signal(signal.SIGINT, _signal_handler)
    with _total_progress_bar(len(files_to_convert)) as pbar:
        for idx, input_file in enumerate(sorted(files_to_convert)):
            convert_file(
                file_name=input_file,
                prefered_bitrate=prefered_bitrate,
                file_container=file_container,
                keep_files=keep_files,
                vbr=vbr,
                mp3=mp3,
                input_root=input_path,
                output_dir=output_dir,
            )
            pbar.postfix = f"{idx + 1}/{len(files_to_convert)}"
            pbar.update(1)
