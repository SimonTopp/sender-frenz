"""Tests for sender_frenz.space_builder.room."""

import dataclasses
from uuid import uuid4

import pytest

from sender_frenz.common.models import Room
from sender_frenz.common.types import AvatarId, RoomId
from sender_frenz.space_builder.room import BARE_ROOM_LEVEL, create_room

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _room_id() -> RoomId:
    return RoomId(uuid4())


def _avatar_id() -> AvatarId:
    return AvatarId(uuid4())


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestBareRoomConstants:
    def test_bare_room_level_is_zero(self) -> None:
        assert BARE_ROOM_LEVEL == 0


# ---------------------------------------------------------------------------
# create_room — return type
# ---------------------------------------------------------------------------


class TestCreateRoomReturnType:
    def test_returns_room_instance(self) -> None:
        room = create_room(_room_id(), _avatar_id())
        assert isinstance(room, Room)


# ---------------------------------------------------------------------------
# create_room — identity fields
# ---------------------------------------------------------------------------


class TestCreateRoomIdentity:
    def test_room_id_preserved(self) -> None:
        rid = _room_id()
        room = create_room(rid, _avatar_id())
        assert room.id == rid

    def test_avatar_id_preserved(self) -> None:
        aid = _avatar_id()
        room = create_room(_room_id(), aid)
        assert room.avatar_id == aid

    def test_different_ids_produce_independent_rooms(self) -> None:
        rid_a, rid_b = _room_id(), _room_id()
        assert rid_a != rid_b
        room_a = create_room(rid_a, _avatar_id())
        room_b = create_room(rid_b, _avatar_id())
        assert room_a.id != room_b.id

    def test_same_avatar_can_have_distinct_rooms(self) -> None:
        aid = _avatar_id()
        room_a = create_room(_room_id(), aid)
        room_b = create_room(_room_id(), aid)
        assert room_a.avatar_id == room_b.avatar_id
        assert room_a.id != room_b.id


# ---------------------------------------------------------------------------
# create_room — initial state
# ---------------------------------------------------------------------------


class TestCreateRoomInitialState:
    def test_initial_level_is_bare_room_level(self) -> None:
        room = create_room(_room_id(), _avatar_id())
        assert room.level == BARE_ROOM_LEVEL

    def test_no_applied_upgrades_on_creation(self) -> None:
        room = create_room(_room_id(), _avatar_id())
        assert room.applied_upgrades == ()

    def test_applied_upgrades_is_tuple(self) -> None:
        room = create_room(_room_id(), _avatar_id())
        assert isinstance(room.applied_upgrades, tuple)


# ---------------------------------------------------------------------------
# create_room — immutability
# ---------------------------------------------------------------------------


class TestCreateRoomImmutability:
    def test_room_is_frozen_dataclass(self) -> None:
        room = create_room(_room_id(), _avatar_id())
        assert dataclasses.is_dataclass(room)
        with pytest.raises(dataclasses.FrozenInstanceError):
            room.level = 1  # type: ignore[misc]

    def test_room_applied_upgrades_is_immutable_tuple(self) -> None:
        room = create_room(_room_id(), _avatar_id())
        # Tuples do not support item assignment.
        with pytest.raises(TypeError):
            room.applied_upgrades[0] = "slug"  # type: ignore[index]
