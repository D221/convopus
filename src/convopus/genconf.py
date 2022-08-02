'''Generates default config file'''
import json
import os
import sys
from appdirs import user_config_dir

APP_NAME = "convopus"
APP_AUTHOR = "D221"
config = {
    "BITRATE": "128k",
    "CONTAINER": ".ogg",
    "KEEP": True,
    "VBR": 'on',
    "COMMONTYPES": ('.flac', '.mp3', '.wav', '.m4a',
                    '.aac', '.webm', '.mp4', '.avi', '.mkv')
}

conf_path = user_config_dir(APP_NAME, APP_AUTHOR)
CONF_FILE = 'config.json'
conf_full_path = os.path.join(conf_path, CONF_FILE)


def generate_config():
    '''Generates configuration file.'''
    os.makedirs(conf_path, exist_ok=True)
    with open(conf_full_path, 'w', encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)


def read_config():
    '''Reads configuration file.'''
    if not os.path.isfile(conf_full_path):
        generate_config()
    with open(conf_full_path, 'r', encoding="utf_8") as config_file:
        config_read = json.load(config_file)
        return config_read


def print_config():
    '''Prints config location and it's content.'''
    print(conf_full_path)
    with open(conf_full_path, 'r', encoding="utf_8") as config_file:
        print(config_file.read())
    sys.exit()
