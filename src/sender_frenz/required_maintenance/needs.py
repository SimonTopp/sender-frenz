"""Need-state predicates and summary for physical avatar health.

These functions are the query side of the maintenance loop: they answer
*how bad is it?* without changing anything.  Use them in the API layer to
decide which quip triggers to fire and whether to send push notifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sender_frenz.common.thresholds import (
    HUNGER_CRITICAL,
    HUNGER_IDEAL_MAX,
    HYGIENE_CRITICAL,
    HYGIENE_IDEAL_MAX,
)

if TYPE_CHECKING:
    from sender_frenz.common.models import Avatar
    from sender_frenz.common.types import Meter


def is_hungry(avatar: Avatar, threshold: Meter = HUNGER_CRITICAL) -> bool:
    """Return ``True`` when hunger is at or below *threshold*.

    Args:
        avatar: Current avatar state.
        threshold: Hunger value that triggers the hungry flag.
            Defaults to 0.2.

    Returns:
        ``True`` if the avatar needs feeding.
    """
    return avatar.needs.hunger <= threshold


def is_dirty(avatar: Avatar, threshold: Meter = HYGIENE_CRITICAL) -> bool:
    """Return ``True`` when hygiene is at or below *threshold*.

    Args:
        avatar: Current avatar state.
        threshold: Hygiene value that triggers the dirty flag.
            Defaults to 0.2.

    Returns:
        ``True`` if the avatar needs cleaning.
    """
    return avatar.needs.hygiene <= threshold


def is_over_nourished(avatar: Avatar) -> bool:
    """Return ``True`` when hunger exceeds the ideal maximum.

    Args:
        avatar: Current avatar state.

    Returns:
        ``True`` if hunger is above :data:`~.actions.HUNGER_IDEAL_MAX`.
    """
    return avatar.needs.hunger > HUNGER_IDEAL_MAX


def is_over_scrubbed(avatar: Avatar) -> bool:
    """Return ``True`` when hygiene exceeds the ideal maximum.

    Args:
        avatar: Current avatar state.

    Returns:
        ``True`` if hygiene is above :data:`~.actions.HYGIENE_IDEAL_MAX`.
    """
    return avatar.needs.hygiene > HYGIENE_IDEAL_MAX


@dataclass(frozen=True)
class NeedsSummary:
    """Snapshot of the avatar's physical need status.

    All fields are computed from the avatar at summary time.

    Attributes:
        hunger: Current hunger meter value.
        hygiene: Current hygiene meter value.
        hungry: ``True`` when hunger is at or below the critical threshold.
        dirty: ``True`` when hygiene is at or below the critical threshold.
        over_nourished: ``True`` when hunger exceeds the ideal maximum.
        over_scrubbed: ``True`` when hygiene exceeds the ideal maximum.
    """

    hunger: float
    hygiene: float
    hungry: bool
    dirty: bool
    over_nourished: bool
    over_scrubbed: bool


def needs_summary(avatar: Avatar) -> NeedsSummary:
    """Build a :class:`NeedsSummary` from *avatar*'s current state.

    Args:
        avatar: Current avatar state.

    Returns:
        A :class:`NeedsSummary` reflecting the avatar's physical status.
    """
    return NeedsSummary(
        hunger=avatar.needs.hunger,
        hygiene=avatar.needs.hygiene,
        hungry=is_hungry(avatar),
        dirty=is_dirty(avatar),
        over_nourished=is_over_nourished(avatar),
        over_scrubbed=is_over_scrubbed(avatar),
    )
