"""FastAPI application factory.

The module-level ``app`` instance is the ASGI entry point consumed by
uvicorn and by the test client::

    uvicorn sender_frenz.api:app

The ``web/`` directory is served as static files at ``/`` so that a single
``uvicorn`` process handles both the API and the PWA frontend.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from sender_frenz.api.events import EventBus
from sender_frenz.api.routes.action import router as action_router
from sender_frenz.api.routes.level_up import router as level_up_router
from sender_frenz.api.routes.session import router as session_router
from sender_frenz.api.routes.stream import router as stream_router
from sender_frenz.common.config import PRODUCTION_PACE
from sender_frenz.game_loop.scheduler import run_scheduler
from sender_frenz.persistence.store import MemoryStore


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise application state on startup, tear down on shutdown.

    Attaches a :class:`~sender_frenz.persistence.store.MemoryStore`,
    :class:`~sender_frenz.api.events.EventBus`, and
    :data:`~sender_frenz.common.config.PRODUCTION_PACE` to ``app.state``
    so dependency functions can retrieve them without global state.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the application while it serves requests.
    """
    app.state.store = MemoryStore()
    app.state.bus = EventBus()
    app.state.pace = PRODUCTION_PACE
    app.state.scheduler_task = asyncio.create_task(
        run_scheduler(app.state.store, app.state.bus, app.state.pace)
    )
    try:
        yield
    finally:
        app.state.scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await app.state.scheduler_task


app = FastAPI(title="sender-frenz", lifespan=_lifespan)
app.include_router(session_router)
app.include_router(action_router)
app.include_router(level_up_router)
app.include_router(stream_router)
app.mount("/", StaticFiles(directory="web", html=True), name="static")
