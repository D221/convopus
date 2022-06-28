# convert-to-opus-cli

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/D221/convert-to-opus-cli?label=Download)](https://github.com/D221/convert-to-opus-cli/releases/latest)
![GitHub](https://img.shields.io/github/license/D221/convert-to-opus-cli)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/D221/convert-to-opus-cli/Pylint)

convert-to-opus-cli is a Python CLI program for converting audio files to [opus](https://opus-codec.org/) audio format.

![Demo](https://raw.github.com/D221/convert-to-opus-cli/main/demo/demo.gif)

## Features

- Windows / Linux / MacOS / Android (via Termux) support
- Customizable bitrate and more (via config.json)
- Support of various audio formats / containers

## Installation

Must have installed ffmpeg and added to PATH

```bash
git clone https://github.com/D221/convert-to-opus-cli
cd convert-to-opus-cli
pip install -r requirements.txt
```

## Usage

```bash
python3 convert-to-opus-cli -h # for info
# Use -D for directory, -F for a single file
python3 convert-to-opus-cli -D /path/to/files
python3 convert-to-opus-cli -F /path/to/file
```

You can customize settings in config.json

## License

[MIT](https://choosealicense.com/licenses/mit/)
