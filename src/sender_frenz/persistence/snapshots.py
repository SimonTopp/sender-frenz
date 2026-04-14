"""Canonical save unit for one avatar's complete game state.

:class:`GameSnapshot` bundles everything the game loop and API layer need
to reconstruct a full session: the avatar, its room, the interaction
history, and two application-layer timestamps managed by the API layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sender_frenz.common.models import Avatar, Room
    from sender_frenz.common.types import Timestamp
    from sender_frenz.social_maintenance.history import InteractionHistory


@dataclass(frozen=True)
class GameSnapshot:
    """Complete persistent state for one avatar.

    All fields are immutable.  The API layer creates a new snapshot after
    each session or action and passes it to the store.

    Attributes:
        avatar: Current avatar state.
        room: Current room state.
        history: Interaction history log, newest first.
        sustained_since: Timestamp at which the avatar first crossed the
            combined-health threshold in the current level-up streak, or
            ``None`` if the threshold has not been sustained.  Updated by
            the API layer after each session.
        last_tick: Unix epoch timestamp of the most recent processed
            tick.  The API layer uses this to compute elapsed time for
            the next :func:`~sender_frenz.game_loop.tick.process_tick`
            call.
    """

    avatar: Avatar
    room: Room
    history: InteractionHistory
    sustained_since: Timestamp | None
    last_tick: Timestamp
