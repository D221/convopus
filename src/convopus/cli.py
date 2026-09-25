"""Command line interface for convopus."""

import argparse
import os
import subprocess
import sys

from convopus import __version__
from convopus.config import REQUIRED_KEYS, generate_config, print_config, read_config
from convopus.convert import convert_file, convert_folder


def load_config():
    """Read the user config file, validating required keys.

    Offers to regenerate the config when required keys are missing.
    """
    try:
        config_data = read_config()
        for key in REQUIRED_KEYS:
            config_data[key]
    except KeyError:
        print(
            "Config error! Please generate new config\nWould you like to generate a new config file? (Y/N)"
        )
        if input().strip().lower() == "y":
            generate_config()
        sys.exit(0)
    return config_data


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


def parse_arguments(argv, config):
    """Function to parse command-line arguments"""
    # If user needs to view config file, just print and exit gracefully
    parser = argparse.ArgumentParser(
        description="A Python CLI program for converting audio files to opus",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input", nargs="*", default=None, help="Input files or directories (optional)"
    )

    group = parser.add_argument_group(title="Conversion Options")
    group.add_argument(
        "-r",
        "--recursive",
        help="Also convert files in subdirectories",
        action="store_true",
        default=config["RECURSIVE"],
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
        default=config["CONTAINER"],
    )
    group.add_argument(
        "--vbr",
        help="Variable Bitrate option",
        choices=["on", "off"],
        default=config["VBR"],
    )
    group.add_argument(
        "-b",
        "--bitrate",
        help="Preferred bitrate for audio files",
        default=config["BITRATE"],
    )
    group.add_argument(
        "-o",
        "--out",
        metavar="DIRECTORY",
        help="Output directory for converted files (input structure is mirrored under it)",
        default=None,
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
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args(args=argv)
    if args.print_config:
        print_config()
        sys.exit(0)
    return args


def convert(
    input_paths,
    bitrate,
    container,
    keep_files,
    vbr,
    common_types,
    recursive,
    multi_threading,
    mp3,
    out_dir,
):
    """Function that converts audio files into opus format"""
    for input_path in input_paths:
        if os.path.isdir(input_path):
            convert_folder(
                input_path,
                bitrate,
                container,
                keep_files,
                vbr,
                common_types,
                recursive,
                mp3,
                out_dir,
                multi_threading,
            )
        elif os.path.isfile(input_path):
            convert_file(
                input_path,
                bitrate,
                container,
                keep_files,
                vbr,
                mp3,
                input_root=os.path.dirname(input_path) or ".",
                output_dir=out_dir,
            )
        else:
            print(f"The path/file {input_path} is invalid!")


def main():
    """Main function to run the program"""

    config = load_config()
    argv = sys.argv[1:]
    args = parse_arguments(argv, config)
    check_ffmpeg()

    # Set value of keep_files variable based on command-line arguments
    keep_files = None
    if args.keep_original_files:
        keep_files = True
    elif args.delete_original_files:
        keep_files = False
    # If no flag is specified for keep_files, use default value from config file
    if keep_files is None:
        keep_files = config.get("KEEP", True)

    # Set value of multi_threading variable based on command-line arguments
    multi_threading = None
    if args.multithreading:
        multi_threading = True
    elif args.no_multithreading:
        multi_threading = False
    # If no flag is specified for multi_threading, use default value from config file
    if multi_threading is None:
        multi_threading = config.get("MULTI_THREADING")

    if args.input:
        convert(
            args.input,
            args.bitrate,
            args.container,
            keep_files,
            args.vbr,
            config["COMMONTYPES"],
            args.recursive,
            multi_threading,
            args.mp3,
            args.out,
        )
    else:
        print("See convopus --help for usage")


if __name__ == "__main__":
    main()
