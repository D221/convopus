"""Audio conversion: sequential and multiprocessing paths."""

import os
import signal
import subprocess
import sys
import threading
from collections.abc import Callable, Sequence
from functools import partial
from multiprocessing import Pool, cpu_count
from types import FrameType

from tqdm import tqdm

from convopus.outpath import build_output_path, filter_out_dir_files
from ffpb_convopus import ffpb


class ConversionError(RuntimeError):
    """ffmpeg refused to convert a file (nonzero exit status)."""


def _signal_handler(sig: int, frame: FrameType | None) -> None:
    """SIGINT handler: exit like other command-line tools (128 + signal)."""
    raise SystemExit(128 + sig)


def _install_signal_handler() -> None:
    """Install the SIGINT handler when running in the main thread."""
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, _signal_handler)


def _collect_files(
    input_path: str, config_common_types: Sequence[str], recursive: bool
) -> list[str]:
    """List convertible audio files in or below input_path.

    Extensions are compared case-insensitively, so `SONG.FLAC` is picked up
    by the default `.flac` entry.
    """
    extensions = tuple(extension.lower() for extension in config_common_types)
    if recursive:
        return [
            os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(input_path)
            for filename in filenames
            if filename.lower().endswith(extensions)
        ]
    return [
        os.path.join(input_path, filename)
        for filename in os.listdir(input_path)
        if filename.lower().endswith(extensions)
    ]


def _total_progress_bar(total: int, disabled: bool = False) -> tqdm:
    """Create the shared total progress bar."""
    return tqdm(
        total=total,
        desc="Total:",
        dynamic_ncols=True,
        ncols=0,
        colour="green",
        bar_format="{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]",
        disable=disabled,
    )


def _resolve_output_file(
    file_name: str,
    file_container: str,
    mp3: bool,
    input_root: str | None,
    output_dir: str | None,
) -> str:
    """Output next to the input, or mirrored under output_dir when given."""
    if output_dir:
        return build_output_path(
            input_root or ".", file_name, output_dir, file_container, mp3
        )
    if mp3:
        return os.path.splitext(file_name)[0] + ".mp3"
    return os.path.splitext(file_name)[0] + file_container


def _ffmpeg_args(
    file_name: str, output_file: str, prefered_bitrate: str, vbr: str, mp3: bool
) -> list[str]:
    """Shared ffmpeg argument list (without the binary name)."""
    args = [
        "-i",
        file_name,
        "-vn",
        "-c:a",
        "libmp3lame" if mp3 else "libopus",
        "-q:a" if (mp3 and vbr == "on") else None,
        "0" if (mp3 and vbr == "on") else None,  # VBR for MP3
        "-b:a" if (mp3 and vbr == "off") or not mp3 else None,
        "320k" if (mp3 and vbr == "off") else prefered_bitrate if not mp3 else None,
        "-vbr" if not mp3 else None,
        vbr if not mp3 else None,  # VBR for Opus
        output_file,
    ]
    return [arg for arg in args if arg is not None]


def _run_ffmpeg(
    file_name: str,
    output_file: str,
    prefered_bitrate: str,
    vbr: str,
    mp3: bool,
    overwrite: bool,
    progress: bool,
) -> None:
    """Run one ffmpeg conversion and return only on success.

    `progress` selects ffpb (per-file bar) or a plain subprocess (pool and
    --quiet); `overwrite` passes -y so ffmpeg never prompts.
    """
    args = _ffmpeg_args(file_name, output_file, prefered_bitrate, vbr, mp3)
    overwrite_args = ["-y"] if overwrite else []
    if progress:
        returncode = ffpb.main(argv=overwrite_args + args)
    else:
        command = ["ffmpeg"] + overwrite_args + args + ["-loglevel", "error"]
        returncode = subprocess.run(command, check=False).returncode

    if returncode != 0:
        raise ConversionError(f"ffmpeg exited with status {returncode}; original kept")


def convert_file(
    file_name: str,
    prefered_bitrate: str,
    file_container: str,
    keep_files: bool,
    vbr: str,
    mp3: bool,
    input_root: str | None = None,
    output_dir: str | None = None,
    overwrite: bool = False,
    output_file: str | None = None,
) -> None:
    """For converting a single audio file (sequential, with ffpb progress).

    The original is only deleted after ffmpeg reports success: a failed
    conversion (corrupt input, unwritable output, refused overwrite) keeps
    the source file and raises ConversionError. A precomputed `output_file`
    (from plan_conversions) skips path resolution.
    """
    target = output_file or _resolve_output_file(
        file_name, file_container, mp3, input_root, output_dir
    )
    _run_ffmpeg(file_name, target, prefered_bitrate, vbr, mp3, overwrite, progress=True)
    if not keep_files:
        os.remove(file_name)


def _convert_file_direct(
    file_name: str,
    prefered_bitrate: str,
    file_container: str,
    keep_files: bool,
    vbr: str,
    mp3: bool,
    input_root: str | None = None,
    output_dir: str | None = None,
    overwrite: bool = False,
    output_file: str | None = None,
) -> None:
    """Convert one file with subprocess (pool worker or --quiet sequential).

    Same contract as convert_file: raise on failure and keep the original.
    """
    target = output_file or _resolve_output_file(
        file_name, file_container, mp3, input_root, output_dir
    )
    _run_ffmpeg(
        file_name, target, prefered_bitrate, vbr, mp3, overwrite, progress=False
    )
    if not keep_files:
        os.remove(file_name)


def _mt_worker(
    item: tuple[str, str], convert_func: Callable[..., None]
) -> tuple[str, str | None]:
    """Run one pool conversion, reporting failures instead of raising.

    A failing file must not abort the whole batch, so the error travels back
    to the parent as data (the worker process cannot be resumed anyway).
    """
    file_name, output_file = item
    try:
        convert_func(file_name, output_file=output_file)
    except (ConversionError, OSError) as error:
        return file_name, str(error)
    return file_name, None


def _convert_all_mt(
    convert_func: Callable[..., None],
    items: Sequence[tuple[str, str]],
    jobs: int | None = None,
    quiet: bool = False,
) -> list[tuple[str, str]]:
    """Convert planned (input, output) items in a pool; return failures."""
    failures: list[tuple[str, str]] = []
    pool = Pool(jobs or cpu_count())
    try:
        with _total_progress_bar(len(items), disabled=quiet) as pbar:
            for file_name, error in pool.imap_unordered(
                partial(_mt_worker, convert_func=convert_func), items
            ):
                if error is not None:
                    failures.append((file_name, error))
                pbar.update(1)
    except BaseException:
        pool.terminate()
        raise
    else:
        pool.close()
    finally:
        pool.join()
    return failures


def plan_conversions(
    files: Sequence[str],
    file_container: str,
    mp3: bool,
    input_root: str | None,
    output_dir: str | None,
    skip_existing: bool,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Split files into planned (input, output) pairs and skipped files.

    Guards that always apply: an output that would replace an input file, or
    that another input already produces, is skipped rather than silently
    destroying a source or a sibling's result. With `skip_existing`, files
    whose output is already on disk are skipped too.
    """
    conversions: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []
    claimed: set[str] = set()
    input_keys = {os.path.normcase(os.path.abspath(file_name)) for file_name in files}
    for file_name in sorted(files):
        output_file = _resolve_output_file(
            file_name, file_container, mp3, input_root, output_dir
        )
        output_key = os.path.normcase(os.path.abspath(output_file))
        if output_key in input_keys:
            skipped.append(
                (
                    file_name,
                    f"output {output_file} would overwrite an input file",
                )
            )
        elif skip_existing and os.path.isfile(output_file):
            skipped.append((file_name, f"output {output_file} already exists"))
        elif output_key in claimed:
            skipped.append(
                (
                    file_name,
                    f"output {output_file} is already produced by another input",
                )
            )
        else:
            claimed.add(output_key)
            conversions.append((file_name, output_file))
    return conversions, skipped


def report_skipped(skipped: Sequence[tuple[str, str]]) -> None:
    """Print one line per skipped file on stdout."""
    if not skipped:
        return
    noun = "file" if len(skipped) == 1 else "files"
    print(f"Skipped {len(skipped)} {noun}:")
    for file_name, reason in skipped:
        print(f"  {file_name}: {reason}")


def _report_failures(failures: Sequence[tuple[str, str]]) -> None:
    """Print one line per failed file on stderr."""
    if not failures:
        return
    noun = "file" if len(failures) == 1 else "files"
    print(f"{len(failures)} {noun} failed to convert:", file=sys.stderr)
    for file_name, message in failures:
        print(f"  {file_name}: {message}", file=sys.stderr)


def convert_folder(
    input_path: str,
    prefered_bitrate: str,
    file_container: str,
    keep_files: bool,
    vbr: str,
    config_common_types: Sequence[str],
    recursive: bool,
    mp3: bool,
    output_dir: str | None = None,
    multi_threading: bool = False,
    jobs: int | None = None,
    quiet: bool = False,
    overwrite: bool = False,
    skip_existing: bool = False,
) -> int:
    """For converting audio files in a folder.

    Returns the number of files that failed to convert. Failures do not stop
    the batch, and originals are only deleted after a successful conversion.
    `quiet` replaces the per-file ffpb bars with the direct ffmpeg runner and
    disables the total bar; `jobs` caps the worker pool; `overwrite` lets
    ffmpeg replace existing outputs, and `skip_existing` leaves them alone.
    """
    files_to_convert = filter_out_dir_files(
        _collect_files(input_path, config_common_types, recursive), output_dir
    )

    if not files_to_convert:
        print("No files to convert")
        return 0

    conversions, skipped = plan_conversions(
        files_to_convert,
        file_container,
        mp3,
        input_path,
        output_dir,
        skip_existing,
    )
    report_skipped(skipped)
    if not conversions:
        return 0

    _install_signal_handler()
    failures: list[tuple[str, str]] = []
    if multi_threading:
        convert_func = partial(
            _convert_file_direct,
            prefered_bitrate=prefered_bitrate,
            file_container=file_container,
            keep_files=keep_files,
            vbr=vbr,
            mp3=mp3,
            input_root=input_path,
            output_dir=output_dir,
            overwrite=overwrite,
        )
        failures = _convert_all_mt(convert_func, conversions, jobs, quiet)
    else:
        convert_func = _convert_file_direct if quiet else convert_file
        with _total_progress_bar(len(conversions), disabled=quiet) as pbar:
            for idx, (input_file, output_file) in enumerate(conversions):
                try:
                    convert_func(
                        file_name=input_file,
                        prefered_bitrate=prefered_bitrate,
                        file_container=file_container,
                        keep_files=keep_files,
                        vbr=vbr,
                        mp3=mp3,
                        input_root=input_path,
                        output_dir=output_dir,
                        overwrite=overwrite,
                        output_file=output_file,
                    )
                except (ConversionError, OSError) as error:
                    failures.append((input_file, str(error)))
                pbar.postfix = f"{idx + 1}/{len(conversions)}"
                pbar.update(1)

    _report_failures(failures)
    return len(failures)
