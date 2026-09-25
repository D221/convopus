"""Shared fixtures for the convopus test suite."""

import pytest


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Point the config file at a temporary path via CONVOPUS_CONFIG.

    In-process code and subprocesses both honor the override, so every
    test is fully isolated from the real user config.
    """
    config_file = tmp_path / "convopus" / "config.json"
    monkeypatch.setenv("CONVOPUS_CONFIG", str(config_file))
    return config_file


@pytest.fixture
def make_wav(tmp_path):
    """Create short sine-wave .wav files (pure stdlib, no ffmpeg needed)."""

    def _make_wav(name="a.wav", seconds=0.3, parent=None):
        import math
        import struct
        import wave

        parent = tmp_path if parent is None else parent
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
