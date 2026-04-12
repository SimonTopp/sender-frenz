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

Composable decay rules
----------------------
Each :class:`Decay` rule carries a :data:`DecayCondition` predicate.  At
decay time, only rules whose predicate returns ``True`` for the current
avatar contribute to the effective rate.  Base rules use
:func:`_always_active` and are never skipped.  Conditional rules (e.g.
over-nourishment) activate only when the relevant meter exceeds its ideal
maximum.

Pass ``extra_decays`` to :meth:`DecayConfig.from_pace` to inject
conditional penalty decays without modifying the base configuration.
"""

from __future__ import annotations

from collections.abc import Callable
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

# ---------------------------------------------------------------------------
# Composable decay types
# ---------------------------------------------------------------------------

DecayCondition = Callable[[Avatar], bool]
"""Predicate evaluated against the current :class:`Avatar` to decide whether
a :class:`Decay` rule contributes to the effective rate this tick."""


@dataclass(frozen=True)
class Decay:
    """A single composable decay rule.

    Rules are collected into a :class:`DecayConfig` and evaluated at each
    decay tick.  Only rules whose :attr:`condition` returns ``True`` for the
    current avatar are summed into the effective rate.

    Attributes:
        name: Human-readable identifier, e.g. ``"hunger"`` or
            ``"over_nourished"``.
        meter: Meter this rule depletes: ``"hunger"``, ``"hygiene"``, or
            ``"social"``.
        rate_per_hour: Depletion rate in Meter/hour at the configured pace.
        condition: Predicate evaluated against the current avatar.  Use
            :func:`_always_active` for unconditional rules.
    """

    name: str
    meter: str
    rate_per_hour: float
    condition: DecayCondition


def _always_active(avatar: Avatar) -> bool:
    """Return ``True`` unconditionally; used as the base decay condition.

    Args:
        avatar: Current avatar state (unused; present to satisfy the
            :data:`DecayCondition` signature).

    Returns:
        Always ``True``.
    """
    return True


@dataclass(frozen=True)
class DecayConfig:
    """Decay rules and vampiric-advance timing derived from a :class:`GamePace`.

    Do not construct directly in application code; use
    :meth:`from_pace` instead.

    Attributes:
        decays: All active decay rules, base plus any extras injected via
            ``extra_decays``.
        vampiric_advance_hours: Hours at ``score=0.0`` before the vampiric
            stage advances by one step.
        vampiric_retreat_rate: Stages retreated per hour of interaction when
            social score is above zero.
    """

    decays: tuple[Decay, ...]
    vampiric_advance_hours: float
    vampiric_retreat_rate: float

    @classmethod
    def from_pace(
        cls,
        pace: GamePace,
        extra_decays: tuple[Decay, ...] = (),
    ) -> DecayConfig:
        """Derive decay configuration from *pace*.

        Args:
            pace: The game pace to scale rates from.
            extra_decays: Optional conditional penalty rules appended after
                the three base rules.  Use :func:`over_nourished_decay` and
                :func:`over_scrubbed_decay` factories from
                ``required_maintenance.actions`` to construct these.

        Returns:
            A :class:`DecayConfig` with base rates scaled by
            ``pace.time_scale`` and any *extra_decays* appended.
        """
        s = pace.time_scale
        base_decays: tuple[Decay, ...] = (
            Decay(
                name="hunger",
                meter="hunger",
                rate_per_hour=_BASE_HUNGER_RATE * s,
                condition=_always_active,
            ),
            Decay(
                name="hygiene",
                meter="hygiene",
                rate_per_hour=_BASE_HYGIENE_RATE * s,
                condition=_always_active,
            ),
            Decay(
                name="social",
                meter="social",
                rate_per_hour=_BASE_SOCIAL_RATE * s,
                condition=_always_active,
            ),
        )
        return cls(
            decays=(*base_decays, *extra_decays),
            vampiric_advance_hours=_BASE_VAMPIRIC_ADVANCE_HOURS / s,
            vampiric_retreat_rate=_BASE_VAMPIRIC_RETREAT_RATE * s,
        )

    def effective_rate(self, avatar: Avatar, meter: str) -> float:
        """Compute the combined decay rate for *meter* given *avatar*'s state.

        Only rules whose :attr:`~Decay.condition` returns ``True`` against
        *avatar* contribute to the returned rate.

        Args:
            avatar: Current avatar state used to evaluate conditions.
            meter: Meter name: ``"hunger"``, ``"hygiene"``, or ``"social"``.

        Returns:
            Sum of ``rate_per_hour`` for all active decay rules targeting
            *meter*.
        """
        return sum(
            d.rate_per_hour
            for d in self.decays
            if d.meter == meter and d.condition(avatar)
        )


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> Meter:
    return max(lo, min(hi, value))


def apply_need_decay(
    avatar: Avatar,
    elapsed_seconds: float,
    config: DecayConfig,
) -> NeedState:
    """Apply time-based decay to physical need meters.

    The effective hunger and hygiene rates are computed from *config* against
    the current *avatar* state, allowing conditional penalty decays (e.g.
    over-nourishment) to contribute when relevant.

    Args:
        avatar: Current avatar state.
        elapsed_seconds: Seconds elapsed since ``avatar.needs.last_updated``.
        config: Decay configuration to apply.

    Returns:
        A new :class:`NeedState` with updated meters and ``last_updated``
        advanced by *elapsed_seconds*.  Results are clamped to [0.0, 1.0].
    """
    elapsed_hours = elapsed_seconds / _SECONDS_PER_HOUR
    hunger_rate = config.effective_rate(avatar, "hunger")
    hygiene_rate = config.effective_rate(avatar, "hygiene")
    return NeedState(
        hunger=_clamp(avatar.needs.hunger - hunger_rate * elapsed_hours),
        hygiene=_clamp(avatar.needs.hygiene - hygiene_rate * elapsed_hours),
        last_updated=avatar.needs.last_updated + elapsed_seconds,
    )


def apply_social_decay(
    avatar: Avatar,
    elapsed_seconds: float,
    config: DecayConfig,
) -> SocialState:
    """Apply time-based decay to the social health meter and vampiric stage.

    Vampiric stage advances when the social score has been at 0.0 for
    at least ``config.vampiric_advance_hours`` and retreats when the
    score is above 0.0.

    Args:
        avatar: Current avatar state.
        elapsed_seconds: Seconds elapsed since
            ``avatar.social.last_interaction``.
        config: Decay configuration to apply.

    Returns:
        A new :class:`SocialState` with updated score, vampiric stage, and
        ``last_interaction`` advanced by *elapsed_seconds*.
    """
    elapsed_hours = elapsed_seconds / _SECONDS_PER_HOUR
    social_rate = config.effective_rate(avatar, "social")
    new_score = _clamp(avatar.social.score - social_rate * elapsed_hours)

    current_index = vampiric_stage_index(avatar.social.vampiric_stage)

    if new_score == 0.0 and config.vampiric_advance_hours > 0.0:
        # How many full stage advances does the elapsed time represent?
        stages_advanced = int(elapsed_hours / config.vampiric_advance_hours)
        new_index = current_index + stages_advanced
    elif new_score > 0.0 and current_index > 0:
        # Score recovering: retreat at the configured rate.
        stages_retreated = elapsed_hours * config.vampiric_retreat_rate
        new_index = current_index - int(stages_retreated)
    else:
        new_index = current_index

    return SocialState(
        score=new_score,
        vampiric_stage=vampiric_stage_from_index(new_index),
        last_interaction=avatar.social.last_interaction + elapsed_seconds,
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
        config: Decay configuration to apply.

    Returns:
        A new :class:`Avatar` with updated need and social state.
    """
    return Avatar(
        id=avatar.id,
        needs=apply_need_decay(avatar, elapsed_seconds, config),
        social=apply_social_decay(avatar, elapsed_seconds, config),
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
    becomes critical.  Obtain *rate_per_hour* from
    :meth:`DecayConfig.effective_rate` for the current avatar.

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
