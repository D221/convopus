"""Command line interface for convopus."""

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence

from convopus import __version__
from convopus.config import Config, load, print_config
from convopus.convert import (
    ConversionError,
    convert_file,
    convert_folder,
    plan_conversions,
    report_skipped,
)


def check_ffmpeg() -> None:
    """Exit with status 1 unless ffmpeg can be executed."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print(
            "Error: ffmpeg is not installed, not in the system path, or not usable.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


def _container(value: str) -> str:
    """Normalize a container argument to a lowercase `.ext` extension."""
    extension = value.strip().lower()
    if not extension:
        raise argparse.ArgumentTypeError("container must not be empty")
    if not extension.startswith("."):
        extension = f".{extension}"
    return extension


def _bitrate(value: str) -> str:
    """Reject an empty bitrate argument."""
    bitrate = value.strip()
    if not bitrate:
        raise argparse.ArgumentTypeError("bitrate must not be empty")
    return bitrate


def _positive_int(value: str) -> int:
    """Parse a worker count; anything below 1 is rejected."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return number


def parse_arguments(argv: Sequence[str], config: Config) -> argparse.Namespace:
    """Function to parse command-line arguments"""
    # If user needs to view config file, just print and exit gracefully
    parser = argparse.ArgumentParser(
        prog="convopus",
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
        default=config.recursive,
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
        default=config.container,
        type=_container,
    )
    group.add_argument(
        "--vbr",
        help="Variable Bitrate option",
        choices=["on", "off"],
        default=config.vbr,
    )
    group.add_argument(
        "-b",
        "--bitrate",
        help="Preferred bitrate for audio files",
        default=config.bitrate,
        type=_bitrate,
    )
    group.add_argument(
        "-o",
        "--out",
        metavar="DIRECTORY",
        help="Output directory for converted files (input structure is mirrored under it)",
        default=None,
    )
    group.add_argument(
        "-j",
        "--jobs",
        metavar="N",
        type=_positive_int,
        default=None,
        help="Worker processes for multithreading (implies -m; default: CPU count)",
    )
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="No progress bars (useful in logs and scripts)",
    )

    group_existing = group.add_mutually_exclusive_group(required=False)
    group_existing.add_argument(
        "-y",
        "--overwrite",
        action="store_true",
        help="Replace existing output files without asking",
    )
    group_existing.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files whose output already exists",
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
    if args.jobs is not None and args.no_multithreading:
        parser.error("--jobs cannot be combined with --no-multithreading")
    # An explicit existing-file flag overrides both config keys.
    if not args.overwrite and not args.skip_existing:
        args.overwrite = config.overwrite
        args.skip_existing = config.skip_existing
    if args.print_config:
        print_config()  # prints and exits, never returns
    return args


def convert(
    input_paths: Sequence[str],
    bitrate: str,
    container: str,
    keep_files: bool,
    vbr: str,
    common_types: Sequence[str],
    recursive: bool,
    multi_threading: bool,
    mp3: bool,
    out_dir: str | None,
    jobs: int | None = None,
    quiet: bool = False,
    overwrite: bool = False,
    skip_existing: bool = False,
) -> int:
    """Function that converts audio files into opus format.

    Returns the number of paths that failed (invalid input, or a conversion
    error). Failures do not stop the remaining paths.
    """
    failures = 0
    for input_path in input_paths:
        if os.path.isdir(input_path):
            failures += convert_folder(
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
                jobs,
                quiet,
                overwrite,
                skip_existing,
            )
        elif os.path.isfile(input_path):
            input_root = os.path.dirname(input_path) or "."
            conversions, skipped = plan_conversions(
                [input_path], container, mp3, input_root, out_dir, skip_existing
            )
            report_skipped(skipped)
            for file_name, output_file in conversions:
                try:
                    convert_file(
                        file_name,
                        bitrate,
                        container,
                        keep_files,
                        vbr,
                        mp3,
                        input_root=input_root,
                        output_dir=out_dir,
                        overwrite=overwrite,
                        output_file=output_file,
                    )
                except (ConversionError, OSError) as error:
                    print(f"Failed to convert {file_name}: {error}", file=sys.stderr)
                    failures += 1
        else:
            print(f"The path/file {input_path} is invalid!", file=sys.stderr)
            failures += 1
    return failures


def main() -> None:
    """Main function to run the program"""

    config = load()
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
        keep_files = config.keep

    # Set value of multi_threading variable based on command-line arguments
    multi_threading = None
    if args.multithreading:
        multi_threading = True
    elif args.no_multithreading:
        multi_threading = False
    # If no flag is specified for multi_threading, use default value from config file
    if multi_threading is None:
        multi_threading = config.multi_threading
    # --jobs only makes sense with a pool, so it implies -m
    if args.jobs is not None:
        multi_threading = True

    if args.input:
        failures = convert(
            args.input,
            args.bitrate,
            args.container,
            keep_files,
            args.vbr,
            config.common_types,
            args.recursive,
            multi_threading,
            args.mp3,
            args.out,
            args.jobs,
            args.quiet,
            args.overwrite,
            args.skip_existing,
        )
        if failures:
            raise SystemExit(1)
    else:
        print("See convopus --help for usage")


if __name__ == "__main__":
    main()
