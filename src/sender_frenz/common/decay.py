"""Time-based need and social decay engine.

All functions are pure: they take state and elapsed time, return new state.
No randomness, no I/O, no calls to ``time.time()``.  Callers compute
``elapsed_seconds = now - state.last_updated`` and pass it in explicitly.

Pacing
------
Base production rates (``time_scale = 1.0``):

- Hunger empties in  8 h  → 0.1250 Meter/hour
- Hygiene empties in 12 h  → 0.0833 Meter/hour
- Social empties in  24 h  → 0.0417 Meter/hour

All rates scale linearly with :attr:`GamePace.time_scale`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sender_frenz.common.models import (
    Avatar,
    NeedState,
    SocialState,
    vampiric_stage_from_index,
    vampiric_stage_index,
)

if TYPE_CHECKING:
    from sender_frenz.common.config import GamePace
    from sender_frenz.common.types import Meter

# ---------------------------------------------------------------------------
# Base production constants (time_scale = 1.0)
# ---------------------------------------------------------------------------
_BASE_HUNGER_RATE: float = 1.0 / 8.0  # empties in 8 h
_BASE_HYGIENE_RATE: float = 1.0 / 12.0  # empties in 12 h
_BASE_SOCIAL_RATE: float = 1.0 / 24.0  # empties in 24 h
_BASE_VAMPIRIC_ADVANCE_HOURS: float = 12.0  # hours at score=0 per stage
_BASE_VAMPIRIC_RETREAT_RATE: float = 0.5  # stages retreated per interaction-hour

_SECONDS_PER_HOUR: float = 3600.0
_CRITICAL_THRESHOLD: float = 0.2


@dataclass(frozen=True)
class DecayConfig:
    """Decay rates derived from a :class:`GamePace` multiplier.

    Do not construct directly in application code; use
    :meth:`from_pace` instead.

    Attributes:
        hunger_rate: Meter lost per hour.
        hygiene_rate: Meter lost per hour.
        social_rate: Meter lost per hour.
        vampiric_advance_hours: Hours at ``score=0.0`` before vampiric stage advances.
        vampiric_retreat_rate: Stages retreated per hour of interaction.
    """

    hunger_rate: float
    hygiene_rate: float
    social_rate: float
    vampiric_advance_hours: float
    vampiric_retreat_rate: float

    @classmethod
    def from_pace(cls, pace: GamePace) -> DecayConfig:
        """Derive decay rates from *pace*.

        Args:
            pace: The game pace to scale rates from.

        Returns:
            A :class:`DecayConfig` with all rates scaled by
            ``pace.time_scale``.
        """
        s = pace.time_scale
        return cls(
            hunger_rate=_BASE_HUNGER_RATE * s,
            hygiene_rate=_BASE_HYGIENE_RATE * s,
            social_rate=_BASE_SOCIAL_RATE * s,
            vampiric_advance_hours=_BASE_VAMPIRIC_ADVANCE_HOURS / s,
            vampiric_retreat_rate=_BASE_VAMPIRIC_RETREAT_RATE * s,
        )


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> Meter:
    return max(lo, min(hi, value))


def apply_need_decay(
    needs: NeedState,
    elapsed_seconds: float,
    config: DecayConfig,
) -> NeedState:
    """Apply time-based decay to physical need meters.

    Args:
        needs: Current need state.
        elapsed_seconds: Seconds elapsed since ``needs.last_updated``.
        config: Decay rates to apply.

    Returns:
        A new :class:`NeedState` with updated meters and ``last_updated``
        advanced by *elapsed_seconds*.  Results are clamped to [0.0, 1.0].
    """
    elapsed_hours = elapsed_seconds / _SECONDS_PER_HOUR
    return NeedState(
        hunger=_clamp(needs.hunger - config.hunger_rate * elapsed_hours),
        hygiene=_clamp(needs.hygiene - config.hygiene_rate * elapsed_hours),
        last_updated=needs.last_updated + elapsed_seconds,
    )


def apply_social_decay(
    social: SocialState,
    elapsed_seconds: float,
    config: DecayConfig,
) -> SocialState:
    """Apply time-based decay to the social health meter and vampiric stage.

    Vampiric stage advances when the social score has been at 0.0 for
    at least ``config.vampiric_advance_hours`` and retreats when the
    score is above 0.0.

    Args:
        social: Current social state.
        elapsed_seconds: Seconds elapsed since ``social.last_interaction``.
        config: Decay rates to apply.

    Returns:
        A new :class:`SocialState` with updated score, vampiric stage, and
        ``last_interaction`` advanced by *elapsed_seconds*.
    """
    elapsed_hours = elapsed_seconds / _SECONDS_PER_HOUR
    new_score = _clamp(social.score - config.social_rate * elapsed_hours)

    current_index = vampiric_stage_index(social.vampiric_stage)

    if new_score == 0.0 and config.vampiric_advance_hours > 0.0:
        # How many full stage advances does the elapsed time represent?
        stages_advanced = int(elapsed_hours / config.vampiric_advance_hours)
        new_index = current_index + stages_advanced
    elif new_score > 0.0 and current_index > 0:
        # Score recovering: retreat at half the advance rate.
        stages_retreated = elapsed_hours * config.vampiric_retreat_rate
        new_index = current_index - int(stages_retreated)
    else:
        new_index = current_index

    return SocialState(
        score=new_score,
        vampiric_stage=vampiric_stage_from_index(new_index),
        last_interaction=social.last_interaction + elapsed_seconds,
    )


def apply_decay(
    avatar: Avatar,
    elapsed_seconds: float,
    config: DecayConfig,
) -> Avatar:
    """Apply need and social decay to an avatar.

    Convenience wrapper around :func:`apply_need_decay` and
    :func:`apply_social_decay`.

    Args:
        avatar: Current avatar state.
        elapsed_seconds: Seconds elapsed since the avatar was last updated.
        config: Decay rates to apply.

    Returns:
        A new :class:`Avatar` with updated need and social state.
    """
    return Avatar(
        id=avatar.id,
        needs=apply_need_decay(avatar.needs, elapsed_seconds, config),
        social=apply_social_decay(avatar.social, elapsed_seconds, config),
        level=avatar.level,
        created_at=avatar.created_at,
    )


def time_until_critical(
    meter: Meter,
    rate_per_hour: float,
    critical_threshold: float = _CRITICAL_THRESHOLD,
) -> float:
    """Seconds until *meter* crosses *critical_threshold* at *rate_per_hour*.

    Used by the API layer to schedule push notifications before a meter
    becomes critical.

    Args:
        meter: Current meter value in [0.0, 1.0].
        rate_per_hour: Depletion rate in Meter/hour.
        critical_threshold: The threshold that triggers a critical alert.
            Defaults to 0.2.

    Returns:
        Seconds until the meter reaches *critical_threshold*.  Returns
        ``0.0`` if the meter is already at or below the threshold, or if
        *rate_per_hour* is zero.
    """
    if meter <= critical_threshold or rate_per_hour <= 0.0:
        return 0.0
    hours_remaining = (meter - critical_threshold) / rate_per_hour
    return hours_remaining * _SECONDS_PER_HOUR
