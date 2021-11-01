import json

config = {
    "BITRATE": "128k",
    "CONTAINER": ".ogg",
    "KEEP": True,
    "COMMONTYPES": ('.flac', '.mp3', '.wav', '.m4a',
                    '.aac', '.webm', '.mp4', '.avi', '.mkv')
}

with open('config.json', 'w') as f:
    json.dump(config, f, indent=4)
