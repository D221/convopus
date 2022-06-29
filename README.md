# convert-to-opus-cli

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/D221/convert-to-opus-cli?label=Download)](https://github.com/D221/convert-to-opus-cli/releases/latest)
![GitHub](https://img.shields.io/github/license/D221/convert-to-opus-cli)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/D221/convert-to-opus-cli/Pylint)

convert-to-opus-cli is a Python CLI program for converting audio files to [opus](https://opus-codec.org/) audio format.

![Demo](demo/demo.gif)

## Features

- Windows / Linux / MacOS / Android (via Termux) support
- Customizable bitrate and more (via config.json)
- Support of various audio formats / containers

## Installation

Must have installed ffmpeg and added to PATH

```bash
git clone https://github.com/D221/convert-to-opus-cli
```

## Usage

```bash
python3 convert-to-opus-cli -h # for info
# The pogram detects directory or file
python3 convert-to-opus-cli /path/to/directory
python3 convert-to-opus-cli /path/to/file
```

You can customize settings in config.json

## License

[MIT](https://choosealicense.com/licenses/mit/)
