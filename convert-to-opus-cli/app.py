'''Main application for converting audio'''
import json
import os
import shutil
import subprocess

with open('config.json', 'r', encoding="utf_8") as f:
    config = json.load(f)


def convert_folder(input_path):
    '''For converting audio files in a folder'''
    if config['KEEP']:
        keep_location = os.path.join(input_path, 'original')
        os.makedirs(keep_location, exist_ok=True)
    for file_name in os.listdir(input_path):
        if file_name.endswith(tuple(config['COMMONTYPES'])):
            without_ext = os.path.splitext(file_name)[0]
            input_file = os.path.join(input_path, file_name)
            output_file_name = "".join([without_ext, config['CONTAINER']])
            output_file = os.path.join(input_path, output_file_name)
            print(output_file)
            subprocess.call(
                f'ffmpeg -i "{input_file}" -vn -loglevel error -stats -c:a libopus -b:a {config["BITRATE"]} -vbr {config["VBR"]} "{output_file}"')
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
    print(output_file)
    subprocess.call(
        f'ffmpeg -i "{file_name}" -vn -loglevel error -stats -c:a libopus -b:a {config["BITRATE"]} -vbr {config["VBR"]} "{output_file}"')
    if not config['KEEP']:
        os.remove(file_name)
