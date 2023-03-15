'''Main application for converting audio.'''
import os
import subprocess
from functools import partial
from multiprocessing import Pool, cpu_count

from tqdm import tqdm


def convert_folder_mt(input_path, prefered_bitrate, file_container, keep_files, vbr, config_common_types, recursive):
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
    convert_func = partial(convert_file_mt, prefered_bitrate=prefered_bitrate,
                           file_container=file_container, keep_files=keep_files, vbr=vbr)
    with tqdm(total=len(files_to_convert), desc="Total:", dynamic_ncols=True,
              ncols=0, colour='green',
              bar_format='{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]') as pbar:
        for _ in pool.imap_unordered(convert_func, sorted(files_to_convert)):
            pbar.update(1)
    pool.close()
    # implement KeyboardInterrupt


def convert_file_mt(file_name, prefered_bitrate, file_container, keep_files, vbr):
    '''For converting single audio file.'''
    output_file = os.path.join(os.path.splitext(file_name)[0] + file_container)
    ffmpeg_cmd = (['ffmpeg', '-i', file_name, '-vn', '-c:a', 'libopus',
                   '-b:a', prefered_bitrate, '-vbr', vbr, '-loglevel', 'error', output_file])
    subprocess.run(ffmpeg_cmd, check=True)
    if not keep_files:
        os.remove(file_name)
