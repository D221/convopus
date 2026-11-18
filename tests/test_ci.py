"""Guards that keep CI honest about what the suite actually ran."""

import os
import shutil

import pytest


def test_ffmpeg_is_available_in_ci():
    """Fail CI when ffmpeg is missing instead of silently skipping e2e tests."""
    if not os.environ.get("CI"):
        pytest.skip("only enforced in CI")
    assert shutil.which("ffmpeg") is not None, (
        "ffmpeg must be installed in CI: without it every integration test "
        "skips and the job still reports success"
    )
