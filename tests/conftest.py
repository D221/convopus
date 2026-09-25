"""Shared fixtures for the convopus test suite."""

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Redirect the appdirs-based config directory into a temporary one.

    appdirs resolves the Windows config dir through the Win32 shell API,
    which ignores APPDATA/LOCALAPPDATA env overrides — so the resolver
    function itself is patched for in-process code. The env vars are also
    redirected for any code (or subprocess) that falls back to them.
    """
    config_root = tmp_path / "config"
    monkeypatch.setattr(
        "convopus.config.user_config_dir",
        lambda app_name, app_author: str(config_root),
    )
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    return config_root


@pytest.fixture
def make_config():
    """Build a valid config dict with optional overrides."""

    def _make_config(**overrides):
        config = {
            "BITRATE": "128k",
            "CONTAINER": ".opus",
            "KEEP": True,
            "VBR": "on",
            "RECURSIVE": False,
            "MULTI_THREADING": False,
            "COMMONTYPES": [
                ".flac",
                ".mp3",
                ".wav",
                ".m4a",
                ".aac",
                ".webm",
                ".mp4",
                ".avi",
                ".mkv",
                ".mpc",
                ".wma",
            ],
        }
        config.update(overrides)
        return config

    return _make_config


@pytest.fixture
def write_config(isolated_config):
    """Write a config dict as config.json in the isolated config dir."""

    def _write(config):
        from convopus.config import get_config_path

        path = Path(get_config_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def make_wav(tmp_path):
    """Create short sine-wave .wav files (pure stdlib, no ffmpeg needed)."""

    def _make_wav(name="a.wav", seconds=0.3, parent=None):
        import math
        import struct
        import wave

        parent = tmp_path if parent is None else Path(parent)
        path = parent / name
        rate = 8000
        frames = b"".join(
            struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / rate)))
            for i in range(int(rate * seconds))
        )
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            handle.writeframes(frames)
        return path

    return _make_wav
