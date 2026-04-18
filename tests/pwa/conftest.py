"""Playwright test configuration for the sender-frenz PWA.

Prerequisites
-------------
    uv run playwright install chromium

Run with
--------
    uv run pytest tests/pwa

These tests are excluded from the default ``uv run pytest`` run (see
``pyproject.toml`` ``addopts``) because they require a Playwright
Chromium binary that must be installed separately.
"""

import subprocess
import time

import pytest

_PORT = 8765
BASE_URL = f"http://127.0.0.1:{_PORT}"


@pytest.fixture(scope="session")
def live_server():
    """Start the FastAPI + static server once for all PWA tests."""
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "sender_frenz.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(_PORT),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)
    yield BASE_URL
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, object]) -> dict[str, object]:
    """Override default browser context with Pixel 7 mobile profile."""
    return {
        **browser_context_args,
        "viewport": {"width": 412, "height": 915},
        "is_mobile": True,
        "has_touch": True,
        "device_scale_factor": 2.625,
    }
