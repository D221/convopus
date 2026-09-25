"""Configuration file handling: generation, reading, printing."""

import json
import os
import sys

from appdirs import user_config_dir

APP_NAME = "convopus"
APP_AUTHOR = "D221"
CONF_FILE = "config.json"
REQUIRED_KEYS = ("COMMONTYPES", "BITRATE", "CONTAINER", "VBR", "RECURSIVE")

DEFAULT_CONFIG = {
    "BITRATE": "128k",
    "CONTAINER": ".opus",
    "KEEP": True,
    "VBR": "on",
    "RECURSIVE": False,
    "MULTI_THREADING": True,
    "COMMONTYPES": (
        ".flac",
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".webm",
        ".mp4",
        ".avi",
        ".mkv",
        ".mpc",
        ".wma",
    ),
}


def get_config_path():
    """Full path of the user config file, resolved at call time."""
    return os.path.join(user_config_dir(APP_NAME, APP_AUTHOR), CONF_FILE)


def generate_config():
    """Generates configuration file."""
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as config_file:
        json.dump(DEFAULT_CONFIG, config_file, indent=4)


def read_config():
    """Reads configuration file, generating a default one if missing."""
    config_path = get_config_path()
    if not os.path.isfile(config_path):
        generate_config()
    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def print_config():
    """Prints config location and its content."""
    config_path = get_config_path()
    print(config_path)
    with open(config_path, "r", encoding="utf-8") as config_file:
        print(config_file.read())
        sys.exit()


if __name__ == "__main__":
    generate_config()
    print_config()
