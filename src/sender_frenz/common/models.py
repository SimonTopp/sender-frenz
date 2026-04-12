"""Core immutable dataclasses shared across all sender-frenz modules.

Every operation that changes avatar or room state must return a *new*
instance rather than mutating an existing one.  All dataclasses here are
frozen to enforce this at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sender_frenz.common.types import AvatarId, Meter, RoomId, Timestamp


class VampiricStage(Enum):
    """Visual corruption stages driven by social neglect.

    Stages advance when social score remains at zero for an extended
    period and retreat (at half the advance rate) when interactions
    resume.  See :func:`sender_frenz.common.decay.apply_social_decay`.

    Attributes:
        NONE: Healthy social state; no visual corruption.
        PALLOR: Early isolation — skin drains to grey-green, eyes redden.
        GAUNT: Face sharpens, cheekbones protrude, fingers elongate.
        HOLLOW: Eye sockets darken to void, lips recede.
        VAMPIRIC: Full glamour-horror; beautiful and deeply wrong.
    """

    NONE = auto()
    PALLOR = auto()
    GAUNT = auto()
    HOLLOW = auto()
    VAMPIRIC = auto()


# Ordered sequence used for stage arithmetic (advance / retreat).
_VAMPIRIC_STAGES: tuple[VampiricStage, ...] = (
    VampiricStage.NONE,
    VampiricStage.PALLOR,
    VampiricStage.GAUNT,
    VampiricStage.HOLLOW,
    VampiricStage.VAMPIRIC,
)


def vampiric_stage_index(stage: VampiricStage) -> int:
    """Return the 0-based index of *stage* in the progression order.

    Args:
        stage: The stage to look up.

    Returns:
        Integer index in [0, 4].
    """
    return _VAMPIRIC_STAGES.index(stage)


def vampiric_stage_from_index(index: int) -> VampiricStage:
    """Return the stage at *index*, clamped to valid bounds.

    Args:
        index: Raw index (may be out of range; will be clamped).

    Returns:
        The corresponding :class:`VampiricStage`.
    """
    clamped = max(0, min(index, len(_VAMPIRIC_STAGES) - 1))
    return _VAMPIRIC_STAGES[clamped]


@dataclass(frozen=True)
class NeedState:
    """Physical need meters for an avatar.

    Attributes:
        hunger: Fullness level in [0.0, 1.0].  1.0 = satiated, 0.0 = starving.
        hygiene: Cleanliness level in [0.0, 1.0].  1.0 = clean, 0.0 = critical.
        last_updated: Timestamp of the last decay calculation.
    """

    hunger: Meter
    hygiene: Meter
    last_updated: Timestamp

    def __post_init__(self) -> None:
        """Validate meter values are within [0.0, 1.0]."""
        for name, value in (("hunger", self.hunger), ("hygiene", self.hygiene)):
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be in [0.0, 1.0], got {value!r}")


@dataclass(frozen=True)
class SocialState:
    """Social health state for an avatar.

    Attributes:
        score: Social health level in [0.0, 1.0].  1.0 = thriving, 0.0 = isolated.
        vampiric_stage: Current visual corruption level driven by isolation.
        last_interaction: Timestamp of the most recent social interaction.
    """

    score: Meter
    vampiric_stage: VampiricStage
    last_interaction: Timestamp

    def __post_init__(self) -> None:
        """Validate score is within [0.0, 1.0]."""
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score must be in [0.0, 1.0], got {self.score!r}")


@dataclass(frozen=True)
class Level:
    """Avatar progression state.

    Attributes:
        current: Current level number.  0 = bare skeleton; no upper cap.
        skin_upgrades: Slugs of chosen skin upgrades in application order.
        room_upgrades: Slugs of chosen room upgrades in application order.
    """

    current: int
    skin_upgrades: tuple[str, ...]
    room_upgrades: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate level is non-negative."""
        if self.current < 0:
            raise ValueError(f"current level must be >= 0, got {self.current!r}")


@dataclass(frozen=True)
class Avatar:
    """The primary aggregate representing a player's creature.

    All avatar state is immutable.  Every operation that changes avatar
    state must return a new :class:`Avatar` instance.

    Attributes:
        id: Unique avatar identifier.
        needs: Current physical need meters.
        social: Current social health state.
        level: Current progression state.
        created_at: Timestamp when the avatar was first created.
    """

    id: AvatarId
    needs: NeedState
    social: SocialState
    level: Level
    created_at: Timestamp


@dataclass(frozen=True)
class Room:
    """The avatar's personal space, managed independently of the avatar.

    Room level mirrors ``Avatar.level.current`` but is stored here so
    the space domain remains self-contained.

    Attributes:
        id: Unique room identifier.
        avatar_id: The avatar that owns this room.
        level: Room's current level (mirrors avatar level).
        applied_upgrades: Slugs of applied room upgrades in order.
    """

    id: RoomId
    avatar_id: AvatarId
    level: int
    applied_upgrades: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate level is non-negative."""
        if self.level < 0:
            raise ValueError(f"room level must be >= 0, got {self.level!r}")
