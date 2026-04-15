"""Shared fixtures for API tests."""

import random
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from sender_frenz.api.app import app
from sender_frenz.api.deps import (
    get_bus,
    get_now,
    get_pace,
    get_quip_caller,
    get_store,
)
from sender_frenz.api.events import EventBus
from sender_frenz.common.config import FAST_TEST_PACE
from sender_frenz.common.quips import default_quip_caller
from sender_frenz.persistence.store import MemoryStore

FIXED_NOW: float = 1_000_000.0
VALID_UUID = "12345678-1234-5678-1234-567812345678"
VALID_HEADER = {"avatar-id": VALID_UUID}


@pytest.fixture
def fixed_now() -> float:
    return FIXED_NOW


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def quip_caller():
    return default_quip_caller(random.Random(42))


@pytest.fixture
async def client(
    store: MemoryStore,
    bus: EventBus,
    quip_caller,
    fixed_now: float,
) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_bus] = lambda: bus
    app.dependency_overrides[get_pace] = lambda: FAST_TEST_PACE
    app.dependency_overrides[get_now] = lambda: fixed_now
    app.dependency_overrides[get_quip_caller] = lambda: quip_caller
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
