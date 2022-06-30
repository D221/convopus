#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2017-2021 Martin Larralde <martin.larralde@ens-paris-saclay.fr>
# Copyright (c) 2022 D221
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

"""A progress bar for `ffmpeg` using `tqdm`.
"""

import os
import re
import signal
import sys
import subprocess

from tqdm import tqdm


class ProgressNotifier:
    '''Displays progress bar for ffmpeg.'''

    _DURATION_RX = re.compile(b"Duration: (\d{2}):(\d{2}):(\d{2})\.\d{2}")
    _PROGRESS_RX = re.compile(b"time=(\d{2}):(\d{2}):(\d{2})\.\d{2}")
    _OUTPUT_RX = re.compile(b"to '(.*)':")

    @staticmethod
    def _seconds(hours, minutes, seconds):
        return (int(hours) * 60 + int(minutes)) * 60 + int(seconds)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.pbar is not None:
            self.pbar.close()

    def __init__(self, file=None):
        self.lines = []
        self.line_acc = bytearray()
        self.duration = None
        self.source = None
        self.pbar = None
        self.file = file or sys.stderr
        self.encoding = 'UTF-8'

    def __call__(self, char, stdin=None):
        if isinstance(char, str):
            char = char.encode('ascii')
        if char in b"\r\n":
            line = self.newline()
            if self.duration is None:
                self.duration = self.get_duration(line)
            if self.source is None:
                self.source = self.get_output(line)
            self.progress(line)
        else:
            self.line_acc.extend(char)
            if self.line_acc[-6:] == bytearray(b"[y/N] "):
                print(self.line_acc.decode(self.encoding),
                      end="", file=self.file)
                self.file.flush()
                if stdin:
                    stdin.put(input() + "\n")
                self.newline()

    def newline(self):
        '''Prints new line.'''
        line = bytes(self.line_acc)
        self.lines.append(line)
        self.line_acc = bytearray()
        return line

    def get_duration(self, line):
        '''Gets duration from ffmpeg.'''
        search = self._DURATION_RX.search(line)
        if search is not None:
            return self._seconds(*search.groups())
        return None

    def get_output(self, line):
        '''Gets output filename from ffmpeg.'''
        search = self._OUTPUT_RX.search(line)
        if search is not None:
            return os.path.basename(search.group(1).decode(self.encoding))
        return None

    def progress(self, line):
        '''Displays tqdm progress bar.'''
        search = self._PROGRESS_RX.search(line)
        if search is not None:

            total = self.duration  # gets track duration
            current = self._seconds(*search.groups())  # gets current progress

            if self.pbar is None:
                self.pbar = tqdm(
                    desc=self.source,
                    file=self.file,
                    total=total,
                    dynamic_ncols=True,  # dynamicly adjust progress bar length
                    ncols=0,
                    ascii=os.name == "nt",  # windows cmd has problems with unicode
                    bar_format='{l_bar}{bar}|[{elapsed}/{remaining}{postfix}]'
                )

            self.pbar.update(current - self.pbar.n)


def main(argv=None, stream=sys.stderr):
    '''Parse ffmpeg input.'''
    argv = argv or sys.argv[1:]

    try:
        with ProgressNotifier(file=stream) as notifier:

            cmd = ["ffmpeg"] + argv
            _process = subprocess.Popen(cmd, stderr=subprocess.PIPE)

            while True:
                out = _process.stderr.read(1)
                if out == b"" and _process.poll() is not None:
                    break
                if out != b"":
                    notifier(out)

    except KeyboardInterrupt:
        print("Exiting.", file=stream)
        return signal.SIGINT + 128  # POSIX standard

    else:
        if _process.returncode != 0:
            print(notifier.lines[-1].decode(notifier.encoding), file=stream)
        return _process.returncode


if __name__ == "__main__":
    sys.exit(main())
