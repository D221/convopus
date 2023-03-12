'''Main application for converting audio.'''
import os
from multiprocessing import Pool, cpu_count
from functools import partial

from ffpb_convopus import ffpb


def convert_folder(input_path, prefered_bitrate, file_container, keep_files, vbr, config_common_types, recursive):
    '''For converting audio files in a folder.'''
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

    pool = Pool(cpu_count())
    convert_func = partial(convert_file, prefered_bitrate=prefered_bitrate,
                           file_container=file_container, keep_files=keep_files, vbr=vbr)
    for _ in pool.imap_unordered(convert_func, sorted(files_to_convert)):
        pass
    pool.close()


def convert_file(file_name, prefered_bitrate, file_container, keep_files, vbr):
    '''For converting single audio file.'''
    output_file = os.path.join(os.path.splitext(file_name)[0] + file_container)
    ffpb.main(argv=['-i', file_name, '-vn', '-c:a', 'libopus',
                    '-b:a', prefered_bitrate, '-vbr', vbr, output_file])
    if not keep_files:
        os.remove(file_name)
