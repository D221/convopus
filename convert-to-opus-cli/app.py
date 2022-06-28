'''Main application for converting audio'''
from encodings import utf_8
import json
import os
import shutil

import ffpb

with open('config.json', 'r', encoding=utf_8) as f:
    config = json.load(f)


def convert_folder(input_path):
    '''For converting audio files in a folder'''
    if config['KEEP']:
        keep_location = os.path.join(input_path, 'original')
        os.makedirs(keep_location, exist_ok=True)
    for file_name in os.listdir(input_path):
        if file_name.endswith(tuple(config['COMMONTYPES'])):
            without_ext = os.path.splitext(file_name)[0]
            input_file = "".join([input_path, file_name])
            output_file = "".join([input_path, without_ext, config['CONTAINER']])
            ffpb.main(argv=['-i', input_file, '-vn', '-c:a', 'libopus',
                      '-b:a', config['BITRATE'], '-vbr', 'on', output_file])
            if config['KEEP']:
                shutil.move(input_file, keep_location)
            else:
                os.remove(input_file)
        else:
            continue


def convert_file(file_name):
    '''For converting single audio file'''
    without_ext = os.path.splitext(file_name)[0]
    output_file = "".join([without_ext, config['CONTAINER']])
    ffpb.main(argv=['-i', file_name, '-vn', '-c:a', 'libopus',
              '-b:a', config['BITRATE'], '-vbr', 'on', output_file])
    if not config['KEEP']:
        os.remove(file_name)
