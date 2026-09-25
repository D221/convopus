# convopus

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/D221/convopus?label=Download)](https://github.com/D221/convopus/releases/latest)
![GitHub](https://img.shields.io/github/license/D221/convopus)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/D221/convopus/test.yml?branch=main&label=tests)

convopus is a Python CLI program for converting audio files to [opus](https://opus-codec.org/) audio format.

![Demo](https://raw.githubusercontent.com/D221/convopus/main/demo/demo.gif)

## Features

- Windows / Linux / macOS / Android (via Termux) support
- Customizable bitrate, vbr and more (via config.json)
- Support of various input audio formats / containers
- Fast multi threading converting
- Recursive conversion

## Installation

Must have installed ffmpeg and added to PATH

```bash
pip install convopus
```

## Build

```bash
git clone https://github.com/D221/convopus
cd convopus
pip install .
```

## Usage

```bash
convopus -h # for info
# The pogram detects directory or file
convopus /path/to/directory
convopus /path/to/file.flac
```

With `-o/--out DIRECTORY` converted files are written to that directory instead of next to the originals: the input structure is mirrored under it — subfolders are recreated when `-r/--recursive` is used, otherwise files are placed directly in the output directory.
```
usage: convopus [-h] [-r] [--mp3] [-c CONTAINER] [--vbr {on,off}] [-b BITRATE]
                [-o DIRECTORY] [-k | -dk] [-m | -nm] [--config] [-v]
                [input ...]

A Python CLI program for converting audio files to opus

positional arguments:
  input                 Input files or directories (optional) (default: None)

options:
  -h, --help            show this help message and exit
  -k, --keep-original-files
                        Keeps original files after conversion (default: False)
  -dk, --delete-original-files
                        Delete original files after conversion (default:
                        False)
  -m, --multithreading  Use multithreading for faster conversion (default:
                        False)
  -nm, --no-multithreading
                        Do not use multithreading (default: False)
  --config              Prints config location and it's content (default:
                        False)
  -v, --version         show program's version number and exit

Conversion Options:
  -r, --recursive       Also convert files in subdirectories (default: False)
  --mp3                 Convert to mp3 instead - 320 or V0 depending on VBR
                        (default: False)
  -c CONTAINER, --container CONTAINER
                        Container for audio files (.ogg, .opus, .oga, .mkv,
                        .webm) (default: .opus)
  --vbr {on,off}        Variable Bitrate option (default: on)
  -b BITRATE, --bitrate BITRATE
                        Preferred bitrate for audio files (default: 128k)
  -o DIRECTORY, --out DIRECTORY
                        Output directory for converted files (input structure
                        is mirrored under it) (default: None)
```

You can customize settings in **config.json** located in:

|OS|config.json location|
|-|-|
|Windows|%LocalAppData%\D221\convopus|
|Linux|~/.config/convopus|
|macOS|~/Library/Application Support/convopus|

You can override the config file location with the `CONVOPUS_CONFIG` environment variable. Configs from older convopus versions are migrated automatically on first run.

## License

[MIT](https://choosealicense.com/licenses/mit/)
