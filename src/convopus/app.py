'''Main application for converting audio.'''
import os
import shutil
import signal
import sys

from ffpb_convopus import ffpb


def signal_handler(sig, frame):
    '''SIGINT handler.'''
    sys.exit(0)


def convert_folder(input_path, prefered_bitrate, file_container, keep_files, vbr, config_common_types):
    '''For converting audio files in a folder.'''
    if keep_files:
        keep_location = os.path.join(input_path, 'original')
        os.makedirs(keep_location, exist_ok=True)

    signal.signal(signal.SIGINT, signal_handler)
    for file_name in sorted(os.listdir(input_path)):
        if not file_name.endswith(tuple(config_common_types)):
            continue

        without_ext = os.path.splitext(file_name)[0]
        input_file = os.path.join(input_path, file_name)
        output_file_name = "".join([without_ext, file_container])
        output_file = os.path.join(input_path, output_file_name)
        ffpb.main(argv=['-i', input_file, '-vn', '-c:a', 'libopus',
                        '-b:a', prefered_bitrate, '-vbr', vbr, output_file])
        if keep_files:
            shutil.move(input_file, os.path.join(keep_location, file_name))
        else:
            os.remove(input_file)


def convert_file(file_name, prefered_bitrate, file_container, keep_files, vbr):
    '''For converting single audio file.'''
    without_ext = os.path.splitext(file_name)[0]
    output_file = "".join([without_ext, file_container])
    ffpb.main(argv=['-i', file_name, '-vn', '-c:a', 'libopus',
                    '-b:a', prefered_bitrate, '-vbr', vbr, output_file])
    if not keep_files:
        os.remove(file_name)