"""Room factory and bare-room constants.

The single public function here -- :func:`create_room` -- is the only
authorised way to create a new room.  It establishes the canonical bare-room
state that every other module assumes as the starting point.

Bare-room state
---------------
A freshly created room is an empty concrete box: level 0, no furnishings or
decorations applied.  Items are added one per level-up through the level
progression system in :mod:`sender_frenz.common.levels`.

Unlike :func:`sender_frenz.character_builder.avatar.create_avatar`, this factory
requires no timestamp.  :class:`~sender_frenz.common.models.Room` holds no
time-based state -- decay and time tracking live entirely on the avatar side.

Relationship to avatar level
----------------------------
``Room.level`` is intended to mirror ``Avatar.level.current`` at all times.
The factory initialises both to :data:`BARE_ROOM_LEVEL` (0), and
:func:`sender_frenz.common.levels.apply_level_up` increments them together.
Keeping the level on the room allows the space domain to remain self-contained
without referencing the avatar at query time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sender_frenz.common.models import Room

if TYPE_CHECKING:
    from sender_frenz.common.types import AvatarId, RoomId

# ---------------------------------------------------------------------------
# Bare-room constants
# ---------------------------------------------------------------------------

BARE_ROOM_LEVEL: int = 0
"""Level assigned to every newly created room.

Level 0 is the unfurnished base state.  No room upgrades are available until
the room reaches level 1 through the shared level-up flow.
"""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_room(room_id: RoomId, avatar_id: AvatarId) -> Room:
    """Create a new room in bare-room state.

    The room starts at :data:`BARE_ROOM_LEVEL` (0) with no upgrades applied.
    No timestamp is required because :class:`~sender_frenz.common.models.Room`
    contains no time-based fields.

    Args:
        room_id: The unique identifier to assign to this room.  Callers are
            responsible for generating and persisting this value.
        avatar_id: The identifier of the avatar that owns this room.  Used to
            associate the room with its owner without embedding the full avatar.

    Returns:
        A new :class:`~sender_frenz.common.models.Room` in bare-room state.
    """
    return Room(
        id=room_id,
        avatar_id=avatar_id,
        level=BARE_ROOM_LEVEL,
        applied_upgrades=(),
    )
