"""Level progression rules and upgrade catalog interfaces.

This module defines *how* levelling works; the actual catalog content
(skin and room upgrade items) lives in ``character_builder.catalog`` and
``space_builder.catalog``.  Catalogs are injected as arguments so this
module stays decoupled from those packages.

Pacing
------
Production defaults (``time_scale = 1.0``):

- Combined health threshold: 0.75
- Sustain window: 4 hours above threshold before level-up is offered

The sustain window scales inversely with ``time_scale`` so that test and
demo runs are not blocked waiting for a 4-hour window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sender_frenz.common.models import Avatar, Level, Room

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sender_frenz.common.config import GamePace
    from sender_frenz.common.types import Meter, Timestamp

_BASE_THRESHOLD: Meter = 0.75
_BASE_SUSTAIN_HOURS: float = 4.0
_SECONDS_PER_HOUR: float = 3600.0


@dataclass(frozen=True)
class UpgradeOption:
    """A single skin or room upgrade available in the catalog.

    Attributes:
        slug: Machine-readable identifier, e.g. ``"torn-hoodie"``.
        name: Display name following the two-word aesthetic convention,
            e.g. ``"Civic Ruin"``.
        tier: Minimum avatar level required to unlock this option.
        description: Flavor text; must pass the aesthetic guide checklist
            in ``docs/aesthetic.md``.
    """

    slug: str
    name: str
    tier: int
    description: str

    def __post_init__(self) -> None:
        """Validate fields."""
        if not self.slug:
            raise ValueError("slug must not be empty")
        if self.tier < 0:
            raise ValueError(f"tier must be >= 0, got {self.tier!r}")


@dataclass(frozen=True)
class LevelConfig:
    """Level-up timing derived from a :class:`GamePace` multiplier.

    Do not construct directly in application code; use
    :meth:`from_pace` instead.

    Attributes:
        threshold: Combined health score required to qualify for level-up.
        sustain_hours: Hours the threshold must be held before a level-up
            is offered.  Scales inversely with ``time_scale`` so test runs
            are not blocked.
    """

    threshold: Meter
    sustain_hours: float

    @classmethod
    def from_pace(cls, pace: GamePace) -> LevelConfig:
        """Derive level-up timing from *pace*.

        Args:
            pace: The game pace to derive timing from.

        Returns:
            A :class:`LevelConfig` with the threshold unchanged and the
            sustain window compressed by ``pace.time_scale``.
        """
        return cls(
            threshold=_BASE_THRESHOLD,
            sustain_hours=_BASE_SUSTAIN_HOURS / pace.time_scale,
        )


def combined_health(avatar: Avatar) -> Meter:
    """Compute the combined health score for *avatar*.

    The combined score is the arithmetic mean of hunger, hygiene, and
    social score — the single number used to gate level-up eligibility.

    Args:
        avatar: The avatar to evaluate.

    Returns:
        A :class:`Meter` value in [0.0, 1.0].
    """
    return (avatar.needs.hunger + avatar.needs.hygiene + avatar.social.score) / 3.0


def is_level_up_available(
    avatar: Avatar,
    sustained_since: Timestamp,
    now: Timestamp,
    config: LevelConfig,
) -> bool:
    """Return whether a level-up is currently available.

    A level-up is available when combined health is at or above
    ``config.threshold`` *and* it has been held there for at least
    ``config.sustain_hours`` hours.  The sustain requirement prevents
    players from gaming the system with a momentary spike.

    Args:
        avatar: Current avatar state.
        sustained_since: Timestamp at which the avatar first crossed the
            threshold in the current streak.  The caller is responsible
            for tracking this.
        now: Current timestamp.
        config: Level-up timing configuration.

    Returns:
        ``True`` if both conditions are satisfied.
    """
    if combined_health(avatar) < config.threshold:
        return False
    hours_sustained = (now - sustained_since) / _SECONDS_PER_HOUR
    return hours_sustained >= config.sustain_hours


def skin_options_for_level(
    avatar: Avatar,
    catalog: Sequence[UpgradeOption],
) -> tuple[UpgradeOption, ...]:
    """Return skin upgrades available to *avatar* at its current level.

    Filters to options whose tier is at or below the avatar's level and
    whose slug has not already been applied.

    Args:
        avatar: The avatar requesting options.
        catalog: Full skin upgrade catalog.

    Returns:
        Tuple of eligible :class:`UpgradeOption` instances.
    """
    applied = set(avatar.level.skin_upgrades)
    level = avatar.level.current
    return tuple(
        opt for opt in catalog if opt.tier <= level and opt.slug not in applied
    )


def room_options_for_level(
    room: Room,
    catalog: Sequence[UpgradeOption],
) -> tuple[UpgradeOption, ...]:
    """Return room upgrades available to *room* at its current level.

    Filters to options whose tier is at or below the room's level and
    whose slug has not already been applied.

    Args:
        room: The room requesting options.
        catalog: Full room upgrade catalog.

    Returns:
        Tuple of eligible :class:`UpgradeOption` instances.
    """
    applied = set(room.applied_upgrades)
    return tuple(
        opt for opt in catalog if opt.tier <= room.level and opt.slug not in applied
    )


def apply_level_up(
    avatar: Avatar,
    room: Room,
    skin_slug: str,
    room_slug: str,
    skin_catalog: Sequence[UpgradeOption],
    room_catalog: Sequence[UpgradeOption],
) -> tuple[Avatar, Room]:
    """Apply a level-up choice to *avatar* and *room*.

    Increments the level, records the chosen upgrade slugs, and returns
    new immutable instances.

    Args:
        avatar: Current avatar state.
        room: Current room state.
        skin_slug: Slug of the chosen skin upgrade.
        room_slug: Slug of the chosen room upgrade.
        skin_catalog: Full skin upgrade catalog.
        room_catalog: Full room upgrade catalog.

    Returns:
        A ``(new_avatar, new_room)`` tuple with incremented level and
        recorded upgrade choices.

    Raises:
        ValueError: If either slug is not available given the current
            level, or has already been applied.
    """
    available_skins = skin_options_for_level(avatar, skin_catalog)
    available_rooms = room_options_for_level(room, room_catalog)

    available_skin_slugs = {opt.slug for opt in available_skins}
    available_room_slugs = {opt.slug for opt in available_rooms}

    if skin_slug not in available_skin_slugs:
        raise ValueError(
            f"skin slug {skin_slug!r} is not available at level "
            f"{avatar.level.current}. Available: {sorted(available_skin_slugs)}"
        )
    if room_slug not in available_room_slugs:
        raise ValueError(
            f"room slug {room_slug!r} is not available at level "
            f"{room.level}. Available: {sorted(available_room_slugs)}"
        )

    new_level_num = avatar.level.current + 1
    new_avatar = Avatar(
        id=avatar.id,
        needs=avatar.needs,
        social=avatar.social,
        level=Level(
            current=new_level_num,
            skin_upgrades=(*avatar.level.skin_upgrades, skin_slug),
            room_upgrades=(*avatar.level.room_upgrades, room_slug),
        ),
        created_at=avatar.created_at,
    )
    new_room = Room(
        id=room.id,
        avatar_id=room.avatar_id,
        level=new_level_num,
        applied_upgrades=(*room.applied_upgrades, room_slug),
    )
    return new_avatar, new_room
