# convopus

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/D221/convopus?label=Download)](https://github.com/D221/convopus/releases/latest)
![GitHub](https://img.shields.io/github/license/D221/convopus)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/D221/convopus/pylint.yml?branch=main)

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
```
usage: convopus [-h] [-r] [--mp3] [-c CONTAINER] [--vbr {on,off}] [-b BITRATE]
                [-k | -dk] [-m | -nm] [--config] [-v]
                [input]

A Python CLI program for converting audio files to opus

positional arguments:
  input                 Input file or directory (optional) (default: None)

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
```

You can customize settings in **config.json** located in:

|OS|config.json location|
|-|-|
|Windows|%LocalAppData%\D221\convopus|
|Linux|~/.config/convopus|
|macOS|~/Library/Application Support/convopus|

## License

[MIT](https://choosealicense.com/licenses/mit/)
