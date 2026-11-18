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


def _total_progress_bar(total: int) -> tqdm:
    """Create the shared total progress bar."""
    return tqdm(
        total=total,
        desc="Total:",
        dynamic_ncols=True,
        ncols=0,
        colour="green",
        bar_format="{desc} {percentage:3.0f}%|{bar}|[{elapsed}{postfix}]",
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


def convert_file(
    file_name: str,
    prefered_bitrate: str,
    file_container: str,
    keep_files: bool,
    vbr: str,
    mp3: bool,
    input_root: str | None = None,
    output_dir: str | None = None,
) -> None:
    """For converting a single audio file (sequential, with ffpb progress).

    The original is only deleted after ffmpeg reports success: a failed
    conversion (corrupt input, unwritable output, refused overwrite) keeps
    the source file and raises ConversionError.
    """
    output_file = _resolve_output_file(
        file_name, file_container, mp3, input_root, output_dir
    )
    returncode = ffpb.main(
        argv=_ffmpeg_args(file_name, output_file, prefered_bitrate, vbr, mp3)
    )

    if returncode != 0:
        raise ConversionError(f"ffmpeg exited with status {returncode}; original kept")
    if not keep_files:
        os.remove(file_name)


def _convert_file_mt(
    file_name: str,
    prefered_bitrate: str,
    file_container: str,
    keep_files: bool,
    vbr: str,
    mp3: bool,
    input_root: str | None = None,
    output_dir: str | None = None,
) -> None:
    """For converting a single audio file in a worker process.

    Same contract as convert_file: raise on failure and keep the original.
    """
    output_file = _resolve_output_file(
        file_name, file_container, mp3, input_root, output_dir
    )
    ffmpeg_cmd = (
        ["ffmpeg"]
        + _ffmpeg_args(file_name, output_file, prefered_bitrate, vbr, mp3)
        + ["-loglevel", "error"]
    )
    result = subprocess.run(ffmpeg_cmd, check=False)
    if result.returncode != 0:
        raise ConversionError(
            f"ffmpeg exited with status {result.returncode}; original kept"
        )
    if not keep_files:
        os.remove(file_name)


def _mt_worker(
    file_name: str, convert_func: Callable[[str], None]
) -> tuple[str, str | None]:
    """Run one pool conversion, reporting failures instead of raising.

    A failing file must not abort the whole batch, so the error travels back
    to the parent as data (the worker process cannot be resumed anyway).
    """
    try:
        convert_func(file_name)
    except (ConversionError, OSError) as error:
        return file_name, str(error)
    return file_name, None


def _convert_all_mt(
    convert_func: Callable[[str], None], files: Sequence[str]
) -> list[tuple[str, str]]:
    """Convert files in a process pool, returning (file, error) failures."""
    failures: list[tuple[str, str]] = []
    pool = Pool(cpu_count())
    try:
        with _total_progress_bar(len(files)) as pbar:
            for file_name, error in pool.imap_unordered(
                partial(_mt_worker, convert_func=convert_func), files
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


def _report_failures(failures: Sequence[tuple[str, str]]) -> None:
    """Print one line per failed file on stderr."""
    if not failures:
        return
    print(f"{len(failures)} file(s) failed to convert:", file=sys.stderr)
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
) -> int:
    """For converting audio files in a folder.

    Returns the number of files that failed to convert. Failures do not stop
    the batch, and originals are only deleted after a successful conversion.
    """
    files_to_convert = filter_out_dir_files(
        _collect_files(input_path, config_common_types, recursive), output_dir
    )

    if not files_to_convert:
        print("No files to convert")
        return 0

    _install_signal_handler()
    failures: list[tuple[str, str]] = []
    if multi_threading:
        convert_func = partial(
            _convert_file_mt,
            prefered_bitrate=prefered_bitrate,
            file_container=file_container,
            keep_files=keep_files,
            vbr=vbr,
            mp3=mp3,
            input_root=input_path,
            output_dir=output_dir,
        )
        failures = _convert_all_mt(convert_func, sorted(files_to_convert))
    else:
        with _total_progress_bar(len(files_to_convert)) as pbar:
            for idx, input_file in enumerate(sorted(files_to_convert)):
                try:
                    convert_file(
                        file_name=input_file,
                        prefered_bitrate=prefered_bitrate,
                        file_container=file_container,
                        keep_files=keep_files,
                        vbr=vbr,
                        mp3=mp3,
                        input_root=input_path,
                        output_dir=output_dir,
                    )
                except (ConversionError, OSError) as error:
                    failures.append((input_file, str(error)))
                pbar.postfix = f"{idx + 1}/{len(files_to_convert)}"
                pbar.update(1)

    _report_failures(failures)
    return len(failures)
