'''Generates default config file'''
from encodings import utf_8
import json

config = {
    "BITRATE": "128k",
    "CONTAINER": ".ogg",
    "KEEP": True,
    "COMMONTYPES": ('.flac', '.mp3', '.wav', '.m4a',
                    '.aac', '.webm', '.mp4', '.avi', '.mkv')
}

with open('config.json', 'w', encoding=utf_8) as f:
    json.dump(config, f, indent=4)
