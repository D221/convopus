'''Main application for converting audio.'''
import os
import shutil
import signal
import sys

from ffpb import ffpb


def convert_folder(input_path, config_bitrate, config_container, config_keep, config_vbr, config_common_types):
    '''For converting audio files in a folder.'''
    if config_keep:
        keep_location = os.path.join(input_path, 'original')
        os.makedirs(keep_location, exist_ok=True)

    for file_name in sorted(os.listdir(input_path)):
        signal.signal(signal.SIGINT, signal_handler)
        if file_name.endswith(tuple(config_common_types)):
            without_ext = os.path.splitext(file_name)[0]
            input_file = os.path.join(input_path, file_name)
            output_file_name = "".join([without_ext, config_container])
            output_file = os.path.join(input_path, output_file_name)
            ffpb.main(argv=['-i', input_file, '-vn', '-c:a', 'libopus',
                            '-b:a', config_bitrate, '-vbr', config_vbr, output_file])
            if config_keep:
                shutil.move(input_file, keep_location)
            else:
                os.remove(input_file)
        else:
            continue


def convert_file(file_name, config_bitrate, config_container, config_keep, config_vbr):
    '''For converting single audio file.'''
    without_ext = os.path.splitext(file_name)[0]
    output_file = "".join([without_ext, config_container])
    ffpb.main(argv=['-i', file_name, '-vn', '-c:a', 'libopus',
                    '-b:a', config_bitrate, '-vbr', config_vbr, output_file])
    if not config_keep:
        os.remove(file_name)


def signal_handler(sig, frame):
    '''SIGINT handler.'''
    sys.exit(0)
