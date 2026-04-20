"""Feed and clean actions for avatar physical maintenance.

These are the two primary player interactions for managing an avatar's
physical needs.  Both functions are pure — they take current state plus a
timestamp, return a new avatar plus a THE SYSTEM quip.

No I/O, no randomness of their own.  Callers supply the current timestamp
and a :data:`~sender_frenz.common.quips.QuipCaller` (use
:func:`~sender_frenz.common.quips.default_quip_caller` in production).

Over-care penalties
-------------------
Feeding or cleaning past an *ideal maximum* triggers an accelerated decay
when those meters are subsequently processed.  Build the decay config with
the over-care factories and pass it to
:func:`~sender_frenz.common.decay.apply_decay` at each tick::

    from sender_frenz.common.decay import DecayConfig
    from sender_frenz.required_maintenance.actions import (
        over_nourished_decay,
        over_scrubbed_decay,
    )

    config = DecayConfig.from_pace(
        pace,
        extra_decays=(over_nourished_decay(pace), over_scrubbed_decay(pace)),
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sender_frenz.common.models import Avatar, NeedState
from sender_frenz.common.quips import QuipTrigger
from sender_frenz.common.thresholds import HUNGER_IDEAL_MAX, HYGIENE_IDEAL_MAX

if TYPE_CHECKING:
    from sender_frenz.common.config import GamePace
    from sender_frenz.common.decay import Decay
    from sender_frenz.common.quips import QuipCaller
    from sender_frenz.common.types import Timestamp

__all__ = [
    "CLEAN_RESTORE",
    "FEED_RESTORE",
    "HUNGER_IDEAL_MAX",
    "HYGIENE_IDEAL_MAX",
    "ActionResult",
    "clean",
    "feed",
    "over_nourished_decay",
    "over_scrubbed_decay",
]

# ---------------------------------------------------------------------------
# Action restore constants
# ---------------------------------------------------------------------------

FEED_RESTORE: float = 0.40
"""Hunger restored by a single feed action (Meter units)."""

CLEAN_RESTORE: float = 0.50
"""Hygiene restored by a single clean action (Meter units)."""

# ---------------------------------------------------------------------------
# Base over-care decay rates (time_scale = 1.0)
# ---------------------------------------------------------------------------

_BASE_OVER_NOURISHED_RATE: float = 1.0 / 8.0
"""Additional hunger drain rate (Meter/hour) when over-nourished.

Equal to the base hunger rate, so hunger drains at double speed while
over the ideal maximum.
"""

_BASE_OVER_SCRUBBED_RATE: float = 1.0 / 12.0
"""Additional hygiene drain rate (Meter/hour) when over-scrubbed.

Equal to the base hygiene rate, so hygiene drains at double speed while
over the ideal maximum.
"""


# ---------------------------------------------------------------------------
# Decay conditions — satisfy DecayCondition = Callable[[Avatar], bool]
# ---------------------------------------------------------------------------


def _is_over_nourished(avatar: Avatar) -> bool:
    """Return ``True`` when hunger exceeds :data:`HUNGER_IDEAL_MAX`.

    Args:
        avatar: Current avatar state.

    Returns:
        ``True`` if the over-nourished penalty decay should fire.
    """
    return avatar.needs.hunger > HUNGER_IDEAL_MAX


def _is_over_scrubbed(avatar: Avatar) -> bool:
    """Return ``True`` when hygiene exceeds :data:`HYGIENE_IDEAL_MAX`.

    Args:
        avatar: Current avatar state.

    Returns:
        ``True`` if the over-scrubbed penalty decay should fire.
    """
    return avatar.needs.hygiene > HYGIENE_IDEAL_MAX


# ---------------------------------------------------------------------------
# Over-care decay factories
# ---------------------------------------------------------------------------


def over_nourished_decay(pace: GamePace) -> Decay:
    """Build an over-nourishment penalty decay rule for *pace*.

    Inject the returned :class:`~sender_frenz.common.decay.Decay` via
    ``extra_decays`` in :meth:`~sender_frenz.common.decay.DecayConfig.from_pace`.

    Args:
        pace: Game pace used to scale the base rate.

    Returns:
        A :class:`~sender_frenz.common.decay.Decay` that adds extra hunger
        drain whenever hunger exceeds :data:`HUNGER_IDEAL_MAX`.
    """
    from sender_frenz.common.decay import Decay  # avoid circular at module level

    return Decay(
        name="over_nourished",
        meter="hunger",
        rate_per_hour=_BASE_OVER_NOURISHED_RATE * pace.time_scale,
        condition=_is_over_nourished,
    )


def over_scrubbed_decay(pace: GamePace) -> Decay:
    """Build an over-scrubbing penalty decay rule for *pace*.

    Inject the returned :class:`~sender_frenz.common.decay.Decay` via
    ``extra_decays`` in :meth:`~sender_frenz.common.decay.DecayConfig.from_pace`.

    Args:
        pace: Game pace used to scale the base rate.

    Returns:
        A :class:`~sender_frenz.common.decay.Decay` that adds extra hygiene
        drain whenever hygiene exceeds :data:`HYGIENE_IDEAL_MAX`.
    """
    from sender_frenz.common.decay import Decay  # avoid circular at module level

    return Decay(
        name="over_scrubbed",
        meter="hygiene",
        rate_per_hour=_BASE_OVER_SCRUBBED_RATE * pace.time_scale,
        condition=_is_over_scrubbed,
    )


# ---------------------------------------------------------------------------
# Action result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionResult:
    """The outcome of a feed or clean action.

    Attributes:
        avatar: Updated avatar state after the action.
        quip: THE SYSTEM's comment on the action, selected by the caller's
            :data:`~sender_frenz.common.quips.QuipCaller`.
    """

    avatar: Avatar
    quip: str


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def feed(avatar: Avatar, now: Timestamp, quip_caller: QuipCaller) -> ActionResult:
    """Feed the avatar, restoring :data:`FEED_RESTORE` hunger.

    Hunger is clamped to 1.0.  If the result exceeds :data:`HUNGER_IDEAL_MAX`
    the quip trigger is :attr:`~sender_frenz.common.quips.QuipTrigger.OVER_NOURISHED`;
    otherwise :attr:`~sender_frenz.common.quips.QuipTrigger.FEED`.

    Args:
        avatar: Current avatar state.
        now: Current timestamp; recorded as ``needs.last_updated``.
        quip_caller: Quip delivery callable.

    Returns:
        An :class:`ActionResult` with the updated avatar and a quip.
    """
    new_hunger = min(1.0, avatar.needs.hunger + FEED_RESTORE)
    new_needs = NeedState(
        hunger=new_hunger,
        hygiene=avatar.needs.hygiene,
        last_updated=now,
    )
    new_avatar = Avatar(
        id=avatar.id,
        needs=new_needs,
        social=avatar.social,
        level=avatar.level,
        created_at=avatar.created_at,
    )
    trigger = (
        QuipTrigger.OVER_NOURISHED
        if new_hunger > HUNGER_IDEAL_MAX
        else QuipTrigger.FEED
    )
    return ActionResult(avatar=new_avatar, quip=quip_caller(trigger))


def clean(avatar: Avatar, now: Timestamp, quip_caller: QuipCaller) -> ActionResult:
    """Clean the avatar, restoring :data:`CLEAN_RESTORE` hygiene.

    Hygiene is clamped to 1.0.  If the result exceeds :data:`HYGIENE_IDEAL_MAX`
    the quip trigger is :attr:`~sender_frenz.common.quips.QuipTrigger.OVER_SCRUBBED`;
    otherwise :attr:`~sender_frenz.common.quips.QuipTrigger.CLEAN`.

    Args:
        avatar: Current avatar state.
        now: Current timestamp; recorded as ``needs.last_updated``.
        quip_caller: Quip delivery callable.

    Returns:
        An :class:`ActionResult` with the updated avatar and a quip.
    """
    new_hygiene = min(1.0, avatar.needs.hygiene + CLEAN_RESTORE)
    new_needs = NeedState(
        hunger=avatar.needs.hunger,
        hygiene=new_hygiene,
        last_updated=now,
    )
    new_avatar = Avatar(
        id=avatar.id,
        needs=new_needs,
        social=avatar.social,
        level=avatar.level,
        created_at=avatar.created_at,
    )
    trigger = (
        QuipTrigger.OVER_SCRUBBED
        if new_hygiene > HYGIENE_IDEAL_MAX
        else QuipTrigger.CLEAN
    )
    return ActionResult(avatar=new_avatar, quip=quip_caller(trigger))
