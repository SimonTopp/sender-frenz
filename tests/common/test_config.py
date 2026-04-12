"""Tests for sender_frenz.common.config."""

import dataclasses

import pytest

from sender_frenz.common.config import (
    FAST_TEST_PACE,
    PRODUCTION_PACE,
    TEST_PACE,
    GamePace,
)


class TestGamePace:
    def test_production_pace_time_scale(self) -> None:
        assert PRODUCTION_PACE.time_scale == 1.0

    def test_test_pace_time_scale(self) -> None:
        assert TEST_PACE.time_scale == 720.0

    def test_fast_test_pace_time_scale(self) -> None:
        assert FAST_TEST_PACE.time_scale == 43_200.0

    def test_custom_pace(self) -> None:
        pace = GamePace(time_scale=10.0)
        assert pace.time_scale == 10.0

    def test_zero_time_scale_raises(self) -> None:
        with pytest.raises(ValueError, match=r"time_scale must be > 0\.0"):
            GamePace(time_scale=0.0)

    def test_negative_time_scale_raises(self) -> None:
        with pytest.raises(ValueError, match=r"time_scale must be > 0\.0"):
            GamePace(time_scale=-1.0)

    def test_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            PRODUCTION_PACE.time_scale = 99.0  # type: ignore[misc]

    def test_equality(self) -> None:
        assert GamePace(time_scale=1.0) == PRODUCTION_PACE

    def test_inequality(self) -> None:
        assert PRODUCTION_PACE != TEST_PACE
