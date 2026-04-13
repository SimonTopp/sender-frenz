"""Per-avatar interaction history.

Tracks which social interactions an avatar has had and when, providing
query functions used by the game loop to gate achievements, notifications,
and display states.

:class:`InteractionHistory` is a **standalone frozen structure** — it is
not embedded in :class:`~sender_frenz.common.models.Avatar`.  The application
layer holds it alongside the avatar and passes it here for updates and
queries.  This keeps :mod:`sender_frenz.common.models` unchanged.

Events are stored **newest first** so :func:`recent_events` can return
early once a timestamp falls outside the requested window, avoiding a full
scan of the tuple for long histories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sender_frenz.common.types import Timestamp
    from sender_frenz.social_maintenance.interactions import InteractionKind

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InteractionEvent:
    """A single recorded social interaction.

    Attributes:
        kind: The type of interaction that occurred.
        timestamp: Unix epoch time when the interaction was recorded.
    """

    kind: InteractionKind
    timestamp: Timestamp


@dataclass(frozen=True)
class InteractionHistory:
    """An immutable log of social interaction events for one avatar.

    Events are ordered newest first.  All mutations return a new instance;
    the original is never modified.

    Attributes:
        events: Tuple of interaction events, newest first.
    """

    events: tuple[InteractionEvent, ...]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_history() -> InteractionHistory:
    """Create an empty :class:`InteractionHistory`.

    Call this when creating a new avatar to establish its initial
    (empty) interaction log.

    Returns:
        An :class:`InteractionHistory` with no recorded events.
    """
    return InteractionHistory(events=())


# ---------------------------------------------------------------------------
# Mutation (returns new instance)
# ---------------------------------------------------------------------------


def add_event(
    history: InteractionHistory,
    kind: InteractionKind,
    now: Timestamp,
) -> InteractionHistory:
    """Prepend a new interaction event to *history*.

    Args:
        history: Current interaction history.
        kind: The type of interaction that occurred.
        now: Timestamp of the interaction (Unix epoch seconds).

    Returns:
        A new :class:`InteractionHistory` with the event prepended so that
        ``events[0]`` is always the most recent event.
    """
    event = InteractionEvent(kind=kind, timestamp=now)
    return InteractionHistory(events=(event, *history.events))


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def recent_events(
    history: InteractionHistory,
    since: Timestamp,
) -> tuple[InteractionEvent, ...]:
    """Return all events that occurred strictly after *since*.

    Because events are stored newest first, iteration stops as soon as a
    timestamp at or before *since* is encountered.

    Args:
        history: The interaction history to query.
        since: Cutoff timestamp.  Events with ``timestamp <= since`` are
            excluded.

    Returns:
        A tuple of :class:`InteractionEvent` instances with
        ``timestamp > since``, newest first.
    """
    result: list[InteractionEvent] = []
    for event in history.events:
        if event.timestamp <= since:
            break
        result.append(event)
    return tuple(result)


def interactions_in_window(
    history: InteractionHistory,
    since: Timestamp,
) -> int:
    """Return the number of interactions that occurred strictly after *since*.

    Convenience wrapper around :func:`recent_events` for callers that only
    need a count, e.g. to gate achievement notifications.

    Args:
        history: The interaction history to query.
        since: Cutoff timestamp.  Events with ``timestamp <= since`` are
            excluded.

    Returns:
        Count of events with ``timestamp > since``.
    """
    return len(recent_events(history, since))
