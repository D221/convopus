"""Tests for the vendored ffpb progress-wrapper parsing."""

from ffpb_convopus.ffpb import ProgressNotifier


def test_get_duration_parses_timestamp():
    notifier = ProgressNotifier()
    line = b"[mpegts] Duration: 00:01:02.50, start: 1.5"
    assert notifier.get_duration(line) == 62


def test_get_duration_returns_none_when_absent():
    assert ProgressNotifier().get_duration(b"frame= 12 fps=24 q=28.0") is None


def test_get_output_extracts_basename():
    notifier = ProgressNotifier()
    line = b"Output #0, ogg, to 'C:\\music\\song.opus':"
    assert notifier.get_output(line) == "song.opus"


def test_get_output_handles_posix_paths():
    notifier = ProgressNotifier()
    line = b"Output #0, ogg, to '/home/user/music/song.opus':"
    assert notifier.get_output(line) == "song.opus"


def test_get_output_returns_none_when_absent():
    assert ProgressNotifier().get_output(b"Input #0, wav, from 'a.wav':") is None
