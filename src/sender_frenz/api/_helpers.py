"""Application-layer helpers: snapshot bootstrap and sustained_since update.

These functions contain no FastAPI or HTTP coupling and are independently testable.
They encode the application-level contracts that sit above the game engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sender_frenz.character_builder.avatar import create_avatar
from sender_frenz.common.levels import LevelConfig, combined_health
from sender_frenz.common.types import AvatarId, RoomId
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.social_maintenance.history import create_history
from sender_frenz.space_builder.room import create_room

if TYPE_CHECKING:
    from sender_frenz.common.config import GamePace
    from sender_frenz.common.models import Avatar
    from sender_frenz.common.types import Timestamp


def update_sustained_since(
    avatar: Avatar,
    sustained_since: Timestamp | None,
    now: Timestamp,
    pace: GamePace,
) -> Timestamp | None:
    """Recompute sustained_since after any avatar state change.

    Contract (from Phase 7 persistence plan):

    - ``combined_health >= threshold`` and ``sustained_since`` is ``None``
      → set to *now* (streak begins).
    - ``combined_health >= threshold`` and ``sustained_since`` is set
      → carry forward unchanged (streak continues).
    - ``combined_health < threshold`` → ``None`` (streak broken).
    - Level-up callers must pass ``None`` explicitly to reset the streak
      after :func:`~sender_frenz.common.levels.apply_level_up`.

    Args:
        avatar: Updated avatar state after the triggering action.
        sustained_since: Current persisted value (may be ``None``).
        now: Current Unix epoch timestamp.
        pace: Game pace used to derive the level-up health threshold.

    Returns:
        Updated ``sustained_since`` value to persist in the snapshot.
    """
    config = LevelConfig.from_pace(pace)
    if combined_health(avatar) >= config.threshold:
        return sustained_since if sustained_since is not None else now
    return None


def make_snapshot(avatar_id: AvatarId, now: Timestamp) -> GameSnapshot:
    """Create a brand-new :class:`~sender_frenz.persistence.snapshots.GameSnapshot`.

    Called when the store has no existing snapshot for *avatar_id*.
    The returned snapshot is **not** automatically saved to the store;
    the caller decides whether to persist it.

    Args:
        avatar_id: The avatar identifier to assign.
        now: Current Unix epoch timestamp, used for avatar creation timestamps.

    Returns:
        A new :class:`~sender_frenz.persistence.snapshots.GameSnapshot` with a
        fully initialised avatar, a fresh room, an empty interaction history,
        ``sustained_since=None``, and ``last_tick=now``.
    """
    avatar = create_avatar(avatar_id, now)
    room_id = RoomId(uuid4())
    room = create_room(room_id, avatar_id)
    history = create_history()
    return GameSnapshot(
        avatar=avatar,
        room=room,
        history=history,
        sustained_since=None,
        last_tick=now,
    )
