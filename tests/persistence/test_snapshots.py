"""Tests for sender_frenz.persistence.snapshots."""

import dataclasses
from uuid import uuid4

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    Room,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId, RoomId
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.social_maintenance.history import create_history

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _avatar() -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
        social=SocialState(
            score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
        ),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


def _room(avatar_id: AvatarId) -> Room:
    return Room(
        id=RoomId(uuid4()),
        avatar_id=avatar_id,
        level=0,
        applied_upgrades=(),
    )


def _snapshot(
    sustained_since: float | None = None, last_tick: float = 0.0
) -> GameSnapshot:
    av = _avatar()
    return GameSnapshot(
        avatar=av,
        room=_room(av.id),
        history=create_history(),
        sustained_since=sustained_since,
        last_tick=last_tick,
    )


# ---------------------------------------------------------------------------
# GameSnapshot structure
# ---------------------------------------------------------------------------


class TestGameSnapshotStructure:
    def test_is_frozen_dataclass(self) -> None:
        import pytest

        s = _snapshot()
        assert dataclasses.is_dataclass(s)
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.last_tick = 99.0  # type: ignore[misc]

    def test_all_five_fields_present(self) -> None:
        s = _snapshot()
        _ = s.avatar
        _ = s.room
        _ = s.history
        _ = s.sustained_since
        _ = s.last_tick

    def test_avatar_field_type(self) -> None:
        s = _snapshot()
        assert isinstance(s.avatar, Avatar)

    def test_room_field_type(self) -> None:
        s = _snapshot()
        assert isinstance(s.room, Room)

    def test_sustained_since_none_is_valid(self) -> None:
        s = _snapshot(sustained_since=None)
        assert s.sustained_since is None

    def test_sustained_since_float_is_valid(self) -> None:
        s = _snapshot(sustained_since=12345.6)
        assert s.sustained_since == 12345.6

    def test_last_tick_stored(self) -> None:
        s = _snapshot(last_tick=99.5)
        assert s.last_tick == 99.5


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


class TestGameSnapshotEquality:
    def test_equal_snapshots_with_none_sustained_since(self) -> None:
        av = _avatar()
        room = _room(av.id)
        history = create_history()
        s1 = GameSnapshot(
            avatar=av,
            room=room,
            history=history,
            sustained_since=None,
            last_tick=0.0,
        )
        s2 = GameSnapshot(
            avatar=av,
            room=room,
            history=history,
            sustained_since=None,
            last_tick=0.0,
        )
        assert s1 == s2

    def test_snapshots_with_different_last_tick_not_equal(self) -> None:
        av = _avatar()
        room = _room(av.id)
        history = create_history()
        s1 = GameSnapshot(
            avatar=av,
            room=room,
            history=history,
            sustained_since=None,
            last_tick=0.0,
        )
        s2 = GameSnapshot(
            avatar=av,
            room=room,
            history=history,
            sustained_since=None,
            last_tick=1.0,
        )
        assert s1 != s2

    def test_snapshots_with_different_sustained_since_not_equal(self) -> None:
        av = _avatar()
        room = _room(av.id)
        history = create_history()
        s1 = GameSnapshot(
            avatar=av,
            room=room,
            history=history,
            sustained_since=None,
            last_tick=0.0,
        )
        s2 = GameSnapshot(
            avatar=av,
            room=room,
            history=history,
            sustained_since=100.0,
            last_tick=0.0,
        )
        assert s1 != s2
