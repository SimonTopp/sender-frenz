"""SSE stream endpoint: GET /events/{avatar_id}.

Delivers :class:`~sender_frenz.game_loop.tick.GameEvent` instances as
Server-Sent Events to connected clients.  Events are pushed by other endpoints
via :class:`~sender_frenz.api.events.EventBus`; clients receive them in real
time without polling.

The async generator and route handler are excluded from coverage
(``# pragma: no cover``).  Integration testing a live SSE stream is
deferred to Phase 9.

Note: top-level type imports are required so FastAPI's ``get_type_hints()``
can resolve ``Annotated[T, Depends(f)]`` parameter annotations at runtime.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from sender_frenz.api.deps import get_bus
from sender_frenz.api.events import EventBus
from sender_frenz.common.types import AvatarId

if TYPE_CHECKING:
    from sender_frenz.game_loop.tick import GameEvent

router = APIRouter()


async def _sse_generator(  # pragma: no cover
    avatar_id: AvatarId,
    bus: EventBus,
) -> AsyncGenerator[str, None]:
    r"""Yield SSE-formatted strings from the event bus.

    Subscribes to the bus for *avatar_id*, yields one ``data:`` line per
    :class:`~sender_frenz.game_loop.tick.GameEvent`, and closes when a
    ``None`` sentinel is received.

    Args:
        avatar_id: The avatar whose events to stream.
        bus: The event bus to subscribe to.

    Yields:
        SSE-formatted strings of the form ``data: {...}\n\n``.
    """
    queue = bus.subscribe(avatar_id)
    try:
        while True:
            event: GameEvent | None = await queue.get()
            if event is None:
                break
            payload = json.dumps(
                {"kind": event.kind.value, "timestamp": event.timestamp}
            )
            yield f"data: {payload}\n\n"
    finally:
        bus.unsubscribe(avatar_id, queue)


@router.get("/events/{avatar_id}")  # pragma: no cover
async def events_stream(
    avatar_id: UUID,
    bus: Annotated[EventBus, Depends(get_bus)],
) -> StreamingResponse:
    """Stream game events for *avatar_id* as Server-Sent Events.

    Long-lived HTTP connection.  The client receives one SSE message per
    :class:`~sender_frenz.game_loop.tick.GameEvent` published by any
    state-changing endpoint.

    Args:
        avatar_id: Avatar UUID parsed from the path.
        bus: Event bus dependency.

    Returns:
        A :class:`~fastapi.responses.StreamingResponse` with
        ``Content-Type: text/event-stream``.
    """
    aid = AvatarId(avatar_id)
    return StreamingResponse(
        _sse_generator(aid, bus),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
