"""Main application for converting audio."""

import os
import subprocess
from functools import partial
from multiprocessing import Pool, cpu_count

from tqdm import tqdm

from convopus.outpath import build_output_path, filter_out_dir_files


def convert_folder_mt(
    input_path,
    prefered_bitrate,
    file_container,
    keep_files,
    vbr,
    config_common_types,
    recursive,
    mp3,
    output_dir=None,
):
    """For converting audio files in a folder."""
    files_to_convert = (
        [
            os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(input_path)
            for filename in filenames
            if filename.endswith(tuple(config_common_types))
        ]
        if recursive
        else [
            os.path.join(input_path, filename)
            for filename in os.listdir(input_path)
            if filename.endswith(tuple(config_common_types))
        ]
    )
    files_to_convert = filter_out_dir_files(files_to_convert, output_dir)

    if not files_to_convert:
        print("No files to convert")
        return

    pool = Pool(cpu_count())
    convert_func = partial(
        convert_file_mt,
        prefered_bitrate=prefered_bitrate,
        file_container=file_container,
        keep_files=keep_files,
        vbr=vbr,
        mp3=mp3,
        input_root=input_path,
        output_dir=output_dir,
    )
    with tqdm(
        total=len(files_to_convert),
        desc="Total:",
        dynamic_ncols=True,
        ncols=0,
        colour="green",
        bar_format="{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]",
    ) as pbar:
        for _ in pool.imap_unordered(convert_func, sorted(files_to_convert)):
            pbar.update(1)
    pool.close()
    # implement KeyboardInterrupt


def convert_file_mt(
    file_name,
    prefered_bitrate,
    file_container,
    keep_files,
    vbr,
    mp3,
    input_root=None,
    output_dir=None,
):
    """For converting a single audio file."""
    if output_dir:
        output_file = build_output_path(
            input_root or ".", file_name, output_dir, file_container, mp3
        )
    elif mp3:
        output_file = os.path.splitext(file_name)[0] + ".mp3"
    else:
        output_file = os.path.splitext(file_name)[0] + file_container

    ffmpeg_cmd = [
        "ffmpeg",
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
        "-loglevel",
        "error",
        output_file,
    ]
    ffmpeg_cmd = [arg for arg in ffmpeg_cmd if arg is not None]
    subprocess.run(ffmpeg_cmd, check=True)
    if not keep_files:
        os.remove(file_name)
