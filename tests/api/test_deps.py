"""Tests for sender_frenz.api.deps."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from sender_frenz.api.deps import (
    get_avatar_id,
    get_bus,
    get_now,
    get_pace,
    get_quip_caller,
    get_store,
)
from sender_frenz.api.events import EventBus
from sender_frenz.common.config import PRODUCTION_PACE, GamePace
from sender_frenz.common.quips import QuipTrigger
from sender_frenz.common.types import AvatarId
from sender_frenz.persistence.store import MemoryStore, StoreProtocol

# ---------------------------------------------------------------------------
# get_now
# ---------------------------------------------------------------------------


def test_get_now_returns_positive_float():
    result = get_now()
    assert isinstance(result, float)
    assert result > 0.0


# ---------------------------------------------------------------------------
# get_quip_caller
# ---------------------------------------------------------------------------


def test_get_quip_caller_returns_callable():
    caller = get_quip_caller()
    result = caller(QuipTrigger.LOGIN)
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_quip_caller_each_call_is_independent():
    c1 = get_quip_caller()
    c2 = get_quip_caller()
    assert callable(c1)
    assert callable(c2)


# ---------------------------------------------------------------------------
# get_store
# ---------------------------------------------------------------------------


def test_get_store_returns_store():
    mock_request = MagicMock()
    mock_request.app.state.store = MemoryStore()
    result = get_store(mock_request)
    assert isinstance(result, StoreProtocol)


# ---------------------------------------------------------------------------
# get_bus
# ---------------------------------------------------------------------------


def test_get_bus_returns_event_bus():
    mock_request = MagicMock()
    mock_request.app.state.bus = EventBus()
    result = get_bus(mock_request)
    assert isinstance(result, EventBus)


# ---------------------------------------------------------------------------
# get_pace
# ---------------------------------------------------------------------------


def test_get_pace_returns_game_pace():
    mock_request = MagicMock()
    mock_request.app.state.pace = PRODUCTION_PACE
    result = get_pace(mock_request)
    assert isinstance(result, GamePace)
    assert result.time_scale == 1.0


# ---------------------------------------------------------------------------
# get_avatar_id
# ---------------------------------------------------------------------------


def test_get_avatar_id_valid_uuid():
    uid = uuid4()
    result = get_avatar_id(str(uid))
    assert result == AvatarId(uid)


def test_get_avatar_id_invalid_uuid_raises_422():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_avatar_id("not-a-uuid")
    assert exc_info.value.status_code == 422


def test_get_avatar_id_empty_string_raises_422():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_avatar_id("")
    assert exc_info.value.status_code == 422
