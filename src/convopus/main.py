"""Main program"""

import argparse
import os
import subprocess
import sys

from convopus.app import convert_file, convert_folder
from convopus.app_mt import convert_folder_mt
from convopus.genconf import generate_config, print_config, read_config

# Read config data once
CONFIG_DATA = read_config()
try:
    COMMON_TYPES = CONFIG_DATA["COMMONTYPES"]
    PREFERRED_BITRATE = CONFIG_DATA["BITRATE"]
    CONTAINER = CONFIG_DATA["CONTAINER"]
    VARIABLY_BIT_RATE = CONFIG_DATA["VBR"]
    RECURSIVE = CONFIG_DATA["RECURSIVE"]
    KEEP_FILES = CONFIG_DATA.get("KEEP", True)
    # BETA multithreading only total progress bar , saving original not ideal
    MT = CONFIG_DATA.get("MULTI_THREADING")
except KeyError:
    print(
        "Config error! Please generate new config\nWould you like to generate a new config file? (Y/N)"
    )
    if input().strip().lower() == "y":
        generate_config()
    sys.exit(0)


# check if ffmpeg is installed
def check_ffmpeg():
    """Function to check ffmpeg installation"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except OSError:
        print("Error: ffmpeg is not installed or not in the system path.")
        sys.exit()


def parse_arguments(argv):
    """Function to parse command-line arguments"""
    # If user needs to view config file, just print and exit gracefully
    parser = argparse.ArgumentParser(
        description="A Python CLI program for converting audio files to opus",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input", nargs="?", default=None, help="Input file or directory (optional)"
    )

    group = parser.add_argument_group(title="Conversion Options")
    group.add_argument(
        "-r",
        "--recursive",
        help="Also convert files in subdirectories",
        action="store_true",
        default=RECURSIVE,
    )
    group.add_argument(
        "--mp3",
        help="Convert to mp3 instead - 320 or V0 depending on VBR",
        action="store_true",
    )
    group.add_argument(
        "-c",
        "--container",
        help="Container for audio files (.ogg, .opus, .oga, .mkv, .webm)",
        default=CONTAINER,
    )
    group.add_argument(
        "--vbr",
        help="Variable Bitrate option",
        choices=["on", "off"],
        default=VARIABLY_BIT_RATE,
    )
    group.add_argument(
        "-b",
        "--bitrate",
        help="Preferred bitrate for audio files",
        default=PREFERRED_BITRATE,
    )

    action_group_keep = parser.add_mutually_exclusive_group(required=False)
    action_group_keep.add_argument(
        "-k",
        "--keep-original-files",
        action="store_true",
        help="Keeps original files after conversion",
    )
    action_group_keep.add_argument(
        "-dk",
        "--delete-original-files",
        action="store_true",
        help="Delete original files after conversion",
    )

    action_group_mt = parser.add_mutually_exclusive_group(required=False)
    action_group_mt.add_argument(
        "-m",
        "--multithreading",
        help="Use multithreading for faster conversion",
        action="store_true",
    )
    action_group_mt.add_argument(
        "-nm",
        "--no-multithreading",
        help="Do not use multithreading",
        action="store_true",
    )

    parser.add_argument(
        "--config",
        help="Prints config location and it's content",
        action="store_true",
        dest="print_config",
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.4.2")

    args = parser.parse_args(args=argv)
    # if user wants to see the config, retrieve and display it
    if args.print_config:
        print_config()
        sys.exit(0)
    return args


def convert(
    input_path,
    bitrate,
    container,
    keep_files,
    vbr,
    common_types,
    recursive,
    multi_threading,
    mp3,
):
    """Function that converts audio files into opus format"""
    if os.path.isdir(input_path):
        if multi_threading:
            convert_folder_mt(
                input_path,
                bitrate,
                container,
                keep_files,
                vbr,
                common_types,
                recursive,
                mp3,
            )
        else:
            convert_folder(
                input_path,
                bitrate,
                container,
                keep_files,
                vbr,
                common_types,
                recursive,
                mp3,
            )
    elif os.path.isfile(input_path):
        convert_file(input_path, bitrate, container, keep_files, vbr, mp3)
    else:
        print(f"The path/file {input_path} is invalid!")
        sys.exit(1)


def main():
    """Main function to run the program"""

    argv = sys.argv[1:]
    args = parse_arguments(argv)
    check_ffmpeg()

    # Set value of keep_files variable based on command-line arguments
    keep_files = None
    if args.keep_original_files:
        keep_files = True
    elif args.delete_original_files:
        keep_files = False
    # If no flag is specified for keep_files, use default value from config file
    if keep_files is None:
        keep_files = KEEP_FILES

    # Set value of multi_threading variable based on command-line arguments
    multi_threading = None
    if args.multithreading:
        multi_threading = True
    elif args.no_multithreading:
        multi_threading = False
    # If no flag is specified for multi_threading, use default value from config file
    if multi_threading is None:
        multi_threading = MT
    if len(sys.argv) > 1:
        convert(
            args.input,
            args.bitrate,
            args.container,
            keep_files,
            args.vbr,
            COMMON_TYPES,
            args.recursive,
            multi_threading,
            args.mp3,
        )
    else:
        print("See convopus --help for usage")


if __name__ == "__main__":
    main()
