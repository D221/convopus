"""Tests for the shared ffmpeg argument builder."""

from convopus.convert import _ffmpeg_args


def test_opus_default_vbr_on():
    assert _ffmpeg_args("song.wav", "song.opus", "128k", "on", False) == [
        "-i",
        "song.wav",
        "-vn",
        "-c:a",
        "libopus",
        "-b:a",
        "128k",
        "-vbr",
        "on",
        "song.opus",
    ]


def test_opus_vbr_off():
    args = _ffmpeg_args("song.wav", "song.opus", "96k", "off", False)
    assert args == [
        "-i",
        "song.wav",
        "-vn",
        "-c:a",
        "libopus",
        "-b:a",
        "96k",
        "-vbr",
        "off",
        "song.opus",
    ]


def test_mp3_vbr_on_uses_quality_0():
    args = _ffmpeg_args("song.wav", "song.mp3", "128k", "on", True)
    assert args == [
        "-i",
        "song.wav",
        "-vn",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "0",
        "song.mp3",
    ]


def test_mp3_vbr_off_uses_320k():
    args = _ffmpeg_args("song.wav", "song.mp3", "128k", "off", True)
    assert args == [
        "-i",
        "song.wav",
        "-vn",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "320k",
        "song.mp3",
    ]


def test_bitrate_is_passed_through_for_opus():
    args = _ffmpeg_args("song.wav", "song.opus", "192k", "on", False)
    assert "192k" in args
