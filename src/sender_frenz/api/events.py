"""In-memory event bus for Server-Sent Events delivery.

:class:`EventBus` fans out :class:`~sender_frenz.game_loop.tick.GameEvent`
instances to all connected SSE clients registered for a given avatar ID.
One :class:`asyncio.Queue` per connected client; events are delivered via
:meth:`EventBus.publish` and consumed by the SSE generator in
:mod:`sender_frenz.api.routes.stream`.

Not thread-safe.  All FastAPI route handlers share the same asyncio event
loop; no locking is required.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sender_frenz.common.types import AvatarId
    from sender_frenz.game_loop.tick import GameEvent


class EventBus:
    """Fan-out event bus: avatar_id → list of subscriber queues.

    Each call to :meth:`subscribe` registers a new
    :class:`asyncio.Queue` for the given avatar.  :meth:`publish`
    enqueues events to every registered queue.  :meth:`unsubscribe`
    removes a queue when its client disconnects.

    A sentinel value of ``None`` in a queue signals the SSE generator to
    close the connection.
    """

    def __init__(self) -> None:
        """Initialise an empty bus with no subscribers."""
        self._queues: dict[AvatarId, list[asyncio.Queue[GameEvent | None]]] = {}

    def subscribe(self, avatar_id: AvatarId) -> asyncio.Queue[GameEvent | None]:
        """Register a new subscriber queue for *avatar_id*.

        Args:
            avatar_id: The avatar whose events the caller wants to receive.

        Returns:
            A fresh :class:`asyncio.Queue` that will receive future events
            published for *avatar_id* and a ``None`` close sentinel.
        """
        if avatar_id not in self._queues:
            self._queues[avatar_id] = []
        queue: asyncio.Queue[GameEvent | None] = asyncio.Queue()
        self._queues[avatar_id].append(queue)
        return queue

    def unsubscribe(
        self,
        avatar_id: AvatarId,
        queue: asyncio.Queue[GameEvent | None],
    ) -> None:
        """Remove *queue* from the subscribers for *avatar_id*.

        Safe to call even if *queue* has already been removed.  Cleans up
        the entry for *avatar_id* when its subscriber list becomes empty.

        Args:
            avatar_id: The avatar whose subscriber list to update.
            queue: The queue to remove.
        """
        if avatar_id not in self._queues:
            return
        try:
            self._queues[avatar_id].remove(queue)
        except ValueError:
            return
        if not self._queues[avatar_id]:
            del self._queues[avatar_id]

    def publish(
        self,
        avatar_id: AvatarId,
        events: Iterable[GameEvent],
    ) -> None:
        """Push *events* to all subscriber queues for *avatar_id*.

        No-op when there are no subscribers.  Events are enqueued via
        :meth:`~asyncio.Queue.put_nowait`; queues are unbounded, so this
        never blocks.

        Args:
            avatar_id: The avatar whose subscribers should receive the events.
            events: Iterable of :class:`~sender_frenz.game_loop.tick.GameEvent`
                instances to deliver.
        """
        if avatar_id not in self._queues:
            return
        for event in events:
            for queue in self._queues[avatar_id]:
                queue.put_nowait(event)
