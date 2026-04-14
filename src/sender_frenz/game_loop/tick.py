"""Headless state-advancement engine for the game loop.

Applies time-based decay to an avatar and records what changed as a
tuple of :class:`GameEvent` instances — the canonical animation contract
consumed by the display layer.

Events are only emitted when a threshold is *newly* crossed: a meter
that was already below a threshold before the tick does not re-emit the
corresponding event.  Needs and social decay are computed with separate
elapsed times so each subsystem advances from its own last-updated
timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from sender_frenz.common.decay import DecayConfig, apply_need_decay, apply_social_decay
from sender_frenz.common.models import Avatar, vampiric_stage_index

if TYPE_CHECKING:
    from sender_frenz.common.config import GamePace
    from sender_frenz.common.types import Timestamp

# ---------------------------------------------------------------------------
# Threshold constants (aligned with appearance zone boundaries)
# ---------------------------------------------------------------------------

_HUNGER_WARNING_THRESHOLD: float = 0.50  # nourished → hungry zone
_HUNGER_CRITICAL_THRESHOLD: float = 0.20  # hungry → starved zone
_HYGIENE_WARNING_THRESHOLD: float = 0.60  # clean → unkempt zone
_HYGIENE_CRITICAL_THRESHOLD: float = 0.20  # unkempt → grimy zone
_SOCIAL_WARNING_THRESHOLD: float = 0.75  # thriving → middling (THRIVING_THRESHOLD)
_SOCIAL_CRITICAL_THRESHOLD: float = 0.20  # middling → isolated (ISOLATION_THRESHOLD)

# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


class GameEventKind(StrEnum):
    """The type of state change that occurred during a tick.

    Threshold events are emitted only when the boundary is *newly*
    crossed — not on every tick where the meter is already below the
    threshold.
    """

    VAMPIRIC_ADVANCE = "vampiric_advance"
    VAMPIRIC_RETREAT = "vampiric_retreat"
    HUNGER_WARNING = "hunger_warning"
    HUNGER_CRITICAL = "hunger_critical"
    HYGIENE_WARNING = "hygiene_warning"
    HYGIENE_CRITICAL = "hygiene_critical"
    SOCIAL_WARNING = "social_warning"
    SOCIAL_CRITICAL = "social_critical"
    LEVEL_UP_READY = "level_up_ready"


@dataclass(frozen=True)
class GameEvent:
    """A single state-change event emitted during a tick.

    Attributes:
        kind: The type of state change that occurred.
        timestamp: Unix epoch time when the event was detected; equal to
            the ``now`` value passed to :func:`process_tick`.
    """

    kind: GameEventKind
    timestamp: Timestamp


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TickResult:
    """The outcome of applying one tick of decay to an avatar.

    Attributes:
        avatar: Updated avatar state after applying decay.
        events: Tuple of :class:`GameEvent` instances describing what
            changed during the tick.  Empty when no thresholds were
            crossed and no stage transitions occurred.
    """

    avatar: Avatar
    events: tuple[GameEvent, ...]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_events(
    before: Avatar,
    after: Avatar,
    now: Timestamp,
) -> tuple[GameEvent, ...]:
    """Compare avatar state before and after decay to produce game events.

    An event is emitted only when a threshold is *newly* crossed — the
    relevant value was on the safe side before the tick and on the
    flagged side after.  Both warning and critical can fire in one tick
    when a meter drops far enough to cross both boundaries.

    Args:
        before: Avatar state before decay was applied.
        after: Avatar state after decay was applied.
        now: Timestamp stamped onto every emitted event.

    Returns:
        Tuple of :class:`GameEvent` instances, one per threshold crossing
        or stage transition detected.
    """
    events: list[GameEvent] = []

    def emit(kind: GameEventKind) -> None:
        events.append(GameEvent(kind=kind, timestamp=now))

    # Vampiric stage transitions
    before_index = vampiric_stage_index(before.social.vampiric_stage)
    after_index = vampiric_stage_index(after.social.vampiric_stage)
    if after_index > before_index:
        emit(GameEventKind.VAMPIRIC_ADVANCE)
    elif after_index < before_index:
        emit(GameEventKind.VAMPIRIC_RETREAT)

    # Hunger threshold crossings (both may fire in one large-drop tick)
    if before.needs.hunger > _HUNGER_WARNING_THRESHOLD >= after.needs.hunger:
        emit(GameEventKind.HUNGER_WARNING)
    if before.needs.hunger > _HUNGER_CRITICAL_THRESHOLD >= after.needs.hunger:
        emit(GameEventKind.HUNGER_CRITICAL)

    # Hygiene threshold crossings
    if before.needs.hygiene > _HYGIENE_WARNING_THRESHOLD >= after.needs.hygiene:
        emit(GameEventKind.HYGIENE_WARNING)
    if before.needs.hygiene > _HYGIENE_CRITICAL_THRESHOLD >= after.needs.hygiene:
        emit(GameEventKind.HYGIENE_CRITICAL)

    # Social threshold crossings
    if before.social.score > _SOCIAL_WARNING_THRESHOLD >= after.social.score:
        emit(GameEventKind.SOCIAL_WARNING)
    if before.social.score > _SOCIAL_CRITICAL_THRESHOLD >= after.social.score:
        emit(GameEventKind.SOCIAL_CRITICAL)

    return tuple(events)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_tick(
    avatar: Avatar,
    now: Timestamp,
    pace: GamePace,
) -> TickResult:
    """Apply time-based decay to *avatar* and detect threshold crossings.

    Needs and social decay are computed with separate elapsed times:
    needs use ``now - avatar.needs.last_updated`` and social uses
    ``now - avatar.social.last_interaction``.  This allows each
    subsystem to decay independently when they were last updated at
    different times.

    Elapsed time is clamped to zero if ``now`` is behind the stored
    timestamp; negative elapsed never mutates state.

    Args:
        avatar: Current avatar state.
        now: Current Unix epoch timestamp.
        pace: Game pace multiplier used to derive decay rates.

    Returns:
        A :class:`TickResult` with the updated avatar and any
        :class:`GameEvent` instances produced by threshold crossings or
        vampiric stage transitions.
    """
    config = DecayConfig.from_pace(pace)

    needs_elapsed = max(0.0, now - avatar.needs.last_updated)
    social_elapsed = max(0.0, now - avatar.social.last_interaction)

    new_needs = apply_need_decay(avatar, needs_elapsed, config)
    new_social = apply_social_decay(avatar, social_elapsed, config)

    new_avatar = Avatar(
        id=avatar.id,
        needs=new_needs,
        social=new_social,
        level=avatar.level,
        created_at=avatar.created_at,
    )

    events = _detect_events(avatar, new_avatar, now)
    return TickResult(avatar=new_avatar, events=events)
