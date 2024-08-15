"""Main application for converting audio."""

import os
import signal
import sys

from tqdm import tqdm

from ffpb_convopus import ffpb


def signal_handler(sig, frame):
    """SIGINT handler."""
    sys.exit(0)


def convert_folder(
    input_path,
    prefered_bitrate,
    file_container,
    keep_files,
    vbr,
    config_common_types,
    recursive,
    mp3,
):
    """For converting audio files in a folder."""
    signal.signal(signal.SIGINT, signal_handler)

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

    if not files_to_convert:
        print("No files to convert")
        return

    with tqdm(
        total=len(files_to_convert),
        desc="Total:",
        dynamic_ncols=True,
        ncols=0,
        colour="green",
        bar_format="{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]",
    ) as pbar:
        for idx, input_file in enumerate(sorted(files_to_convert)):
            convert_file(
                file_name=input_file,
                prefered_bitrate=prefered_bitrate,
                file_container=file_container,
                keep_files=keep_files,
                vbr=vbr,
                mp3=mp3,
            )
            pbar.postfix = f"{idx+1}/{len(files_to_convert)}"
            pbar.update(1)


def convert_file(file_name, prefered_bitrate, file_container, keep_files, vbr, mp3):
    """For converting a single audio file."""
    if mp3:
        output_file = os.path.join(os.path.splitext(file_name)[0] + ".mp3")
    else:
        output_file = os.path.join(os.path.splitext(file_name)[0] + file_container)

    # Select appropriate codec and options
    ffmpeg_cmd = [
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
    # Filter out None values
    ffmpeg_cmd = [arg for arg in ffmpeg_cmd if arg is not None]
    ffpb.main(argv=ffmpeg_cmd)

    if not keep_files:
        os.remove(file_name)
