"""Entry point for running with `python -m convopus`."""

import multiprocessing

from convopus.cli import main

if __name__ == "__main__":
    # Needed by the frozen exe: without it the worker processes spawned by the
    # multiprocessing path re-execute this file and the conversion hangs.
    multiprocessing.freeze_support()
    main()
