"""Tests for sender_frenz.api.app."""

from sender_frenz.api.app import _lifespan, app
from sender_frenz.api.events import EventBus
from sender_frenz.common.config import GamePace
from sender_frenz.persistence.store import MemoryStore


async def test_lifespan_initialises_store():
    async with _lifespan(app):
        assert isinstance(app.state.store, MemoryStore)


async def test_lifespan_initialises_bus():
    async with _lifespan(app):
        assert isinstance(app.state.bus, EventBus)


async def test_lifespan_initialises_pace():
    async with _lifespan(app):
        assert isinstance(app.state.pace, GamePace)
        assert app.state.pace.time_scale == 1.0
