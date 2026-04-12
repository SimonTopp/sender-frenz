"""Game-wide pace configuration.

The single place where production vs. test timing is decided.  All
time-based constants in the game derive from a :class:`GamePace` instance
passed as a parameter — nothing outside this module hardcodes a rate.

Example usage::

    from sender_frenz.common.config import PRODUCTION_PACE, TEST_PACE
    from sender_frenz.common.decay import DecayConfig

    config = DecayConfig.from_pace(PRODUCTION_PACE)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GamePace:
    """Multiplier that scales all time-based game constants.

    Attributes:
        time_scale: Factor applied to base production rates.
            ``1.0`` gives real game timing.  Values above ``1.0``
            compress game time proportionally, allowing the full
            lifecycle to be exercised quickly in tests or demos.

    Raises:
        ValueError: If ``time_scale`` is not strictly positive.
    """

    time_scale: float

    def __post_init__(self) -> None:
        """Validate that time_scale is strictly positive."""
        if self.time_scale <= 0.0:
            raise ValueError(f"time_scale must be > 0.0, got {self.time_scale!r}")


# ---------------------------------------------------------------------------
# Named pace instances — import these rather than constructing GamePace directly
# in application code.
# ---------------------------------------------------------------------------

PRODUCTION_PACE = GamePace(time_scale=1.0)
"""Real game timing.  1 real hour = 1 game hour."""

TEST_PACE = GamePace(time_scale=720.0)
"""Compressed timing for integration tests and demos.
1 real hour ≈ 30 game days, so the full monthly lifecycle fits in ~1 hour."""

FAST_TEST_PACE = GamePace(time_scale=43_200.0)
"""Highly compressed timing for automated smoke tests.
1 real minute ≈ 30 game days."""
