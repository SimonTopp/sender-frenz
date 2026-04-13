"""Avatar factory and skeleton-state constants.

The single public function here — :func:`create_avatar` — is the only
authorised way to create a new avatar.  It establishes the canonical skeleton
state that every other module assumes as the starting point.

Skeleton state
--------------
A freshly created avatar is a bare skeleton: fully topped up on every meter
(hunger, hygiene, social) and at level zero with no upgrades applied.  The
visual corruption pipeline begins at ``VampiricStage.NONE``.

This starting state is intentionally *abundant*: all needs are satisfied so
that the player experiences the game loop of gradual decline before their first
intervention, rather than starting in crisis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)

if TYPE_CHECKING:
    from sender_frenz.common.types import AvatarId, Timestamp

# ---------------------------------------------------------------------------
# Skeleton-state constants
# ---------------------------------------------------------------------------

SKELETON_LEVEL: int = 0
"""Level assigned to every newly created avatar.

Level 0 is the bare-skeleton base state; no skin or room upgrades are
available until the avatar reaches level 1 through the care loop.
"""

INITIAL_METER: float = 1.0
"""Value assigned to every need and social meter on creation.

1.0 represents fully satisfied / healthy.  Decay begins immediately after
creation as the avatar enters the game loop.
"""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_avatar(avatar_id: AvatarId, now: Timestamp) -> Avatar:
    """Create a new avatar in skeleton state.

    All need and social meters are set to :data:`INITIAL_METER` (1.0).
    Vampiric stage is :attr:`~sender_frenz.common.models.VampiricStage.NONE`.
    Level is :data:`SKELETON_LEVEL` (0) with no upgrades.

    The *now* timestamp is recorded as ``created_at``,
    ``needs.last_updated``, and ``social.last_interaction`` so that
    subsequent decay calculations have a consistent starting point.

    Args:
        avatar_id: The unique identifier to assign.  Callers are responsible
            for generating and persisting this value.
        now: Current timestamp (Unix epoch seconds).  Passed explicitly so
            this function remains pure and testable without mocking time.

    Returns:
        A new :class:`~sender_frenz.common.models.Avatar` in skeleton state.
    """
    return Avatar(
        id=avatar_id,
        needs=NeedState(
            hunger=INITIAL_METER,
            hygiene=INITIAL_METER,
            last_updated=now,
        ),
        social=SocialState(
            score=INITIAL_METER,
            vampiric_stage=VampiricStage.NONE,
            last_interaction=now,
        ),
        level=Level(
            current=SKELETON_LEVEL,
            skin_upgrades=(),
            room_upgrades=(),
        ),
        created_at=now,
    )
