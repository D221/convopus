# convert-to-opus-cli

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
# Use -d for directory, -s for single file
python3 convert-to-opus-cli -d /path/to/files
python3 convert-to-opus-cli -s /path/to/file
```

You can customize settings in config.json

## License

[MIT](https://choosealicense.com/licenses/mit/)
