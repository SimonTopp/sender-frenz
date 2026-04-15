"""FastAPI dependency functions for the sender-frenz API.

All application-wide dependencies are defined here.  Tests override them
via ``app.dependency_overrides`` to inject fixed values without touching
``app.state``.

Note: this module intentionally imports at the top level types that are
used in function return annotations — FastAPI calls ``get_type_hints()`` on
dependency functions, so their return types must be resolvable at runtime
(``# noqa: TCH`` in pyproject.toml suppresses the ruff TCH rule here).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import Header, HTTPException, Request

from sender_frenz.api.events import EventBus
from sender_frenz.common.config import GamePace
from sender_frenz.common.quips import QuipCaller, default_quip_caller
from sender_frenz.common.types import AvatarId
from sender_frenz.persistence.store import StoreProtocol

if TYPE_CHECKING:
    from sender_frenz.common.types import Timestamp


def get_store(request: Request) -> StoreProtocol:
    """Return the store from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The :class:`~sender_frenz.persistence.store.StoreProtocol` instance
        attached to ``app.state`` at startup.
    """
    store: StoreProtocol = request.app.state.store
    return store


def get_bus(request: Request) -> EventBus:
    """Return the event bus from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The :class:`~sender_frenz.api.events.EventBus` instance attached
        to ``app.state`` at startup.
    """
    bus: EventBus = request.app.state.bus
    return bus


def get_pace(request: Request) -> GamePace:
    """Return the game pace from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The :class:`~sender_frenz.common.config.GamePace` instance attached
        to ``app.state`` at startup.
    """
    pace: GamePace = request.app.state.pace
    return pace


def get_now() -> Timestamp:
    """Return the current Unix epoch timestamp.

    Returns:
        ``time.time()`` as a :data:`~sender_frenz.common.types.Timestamp`.
    """
    return time.time()


def get_quip_caller() -> QuipCaller:
    """Return a quip caller backed by a fresh unseeded RNG.

    A new :class:`random.Random` is created per request so that quip
    selection is non-deterministic in production.  Tests override this
    dependency with a seeded caller via ``app.dependency_overrides``.

    Returns:
        A :data:`~sender_frenz.common.quips.QuipCaller` backed by
        :func:`~sender_frenz.common.quips.default_quip_caller`.
    """
    return default_quip_caller()


def get_avatar_id(avatar_id: Annotated[str, Header()]) -> AvatarId:
    """Parse the ``Avatar-Id`` header as an ``AvatarId``.

    FastAPI automatically returns 422 when the header is absent.
    This function additionally validates that the value is a well-formed UUID.

    Args:
        avatar_id: Raw header value injected by FastAPI.

    Returns:
        The parsed :class:`~sender_frenz.common.types.AvatarId`.

    Raises:
        :class:`~fastapi.HTTPException` (422): If the header value is not a
            valid UUID.
    """
    try:
        return AvatarId(UUID(avatar_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Avatar-Id is not a valid UUID: {avatar_id!r}",
        ) from exc
