'''Main application for converting audio.'''
import os
import shutil
import signal
import sys

from tqdm import tqdm

from ffpb_convopus import ffpb


def signal_handler(sig, frame):
    '''SIGINT handler.'''
    sys.exit(0)


def convert_folder(input_path, prefered_bitrate, file_container, keep_files, vbr, config_common_types, recursive):
    '''For converting audio files in a folder.'''
    if keep_files:
        keep_location = os.path.join(input_path, 'original')
        os.makedirs(keep_location, exist_ok=True)

    signal.signal(signal.SIGINT, signal_handler)

    files_to_convert = [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(input_path)
        for filename in filenames if filename.endswith(tuple(config_common_types))
    ] if recursive else [
        os.path.join(input_path, filename)
        for filename in os.listdir(input_path) if filename.endswith(tuple(config_common_types))
    ]

    if not files_to_convert:
        print("No files to convert")
        return

    with tqdm(total=len(files_to_convert), desc="Total:", dynamic_ncols=True,
              ncols=0, colour='green',
              bar_format='{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]') as pbar:
        for idx, input_file in enumerate(sorted(files_to_convert)):
            output_file_path = os.path.splitext(input_file)[0] + file_container
            ffpb.main(argv=['-i', input_file, '-vn', '-c:a', 'libopus',
                            '-b:a', prefered_bitrate, '-vbr', vbr, output_file_path])
            if keep_files:
                shutil.move(input_file, keep_location)
            else:
                os.remove(input_file)
            pbar.postfix = f"{idx+1}/{len(files_to_convert)}"
            pbar.update(1)


def convert_file(file_name, prefered_bitrate, file_container, keep_files, vbr):
    '''For converting single audio file.'''
    output_file = os.path.join(os.path.splitext(file_name)[0] + file_container)
    ffpb.main(argv=['-i', file_name, '-vn', '-c:a', 'libopus',
                    '-b:a', prefered_bitrate, '-vbr', vbr, output_file])
    if not keep_files:
        os.remove(file_name)
