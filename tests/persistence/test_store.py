"""Tests for sender_frenz.persistence.store."""

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
from sender_frenz.persistence.store import MemoryStore, StoreProtocol
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


def _snapshot(avatar: Avatar | None = None) -> GameSnapshot:
    if avatar is None:
        avatar = _avatar()
    return GameSnapshot(
        avatar=avatar,
        room=Room(
            id=RoomId(uuid4()),
            avatar_id=avatar.id,
            level=0,
            applied_upgrades=(),
        ),
        history=create_history(),
        sustained_since=None,
        last_tick=0.0,
    )


# ---------------------------------------------------------------------------
# StoreProtocol
# ---------------------------------------------------------------------------


class TestStoreProtocol:
    def test_memory_store_satisfies_protocol(self) -> None:
        store = MemoryStore()
        assert isinstance(store, StoreProtocol)


# ---------------------------------------------------------------------------
# MemoryStore.load
# ---------------------------------------------------------------------------


class TestMemoryStoreLoad:
    def test_returns_none_for_unknown_avatar_id(self) -> None:
        store = MemoryStore()
        unknown_id = AvatarId(uuid4())
        assert store.load(unknown_id) is None

    def test_returns_snapshot_after_save(self) -> None:
        store = MemoryStore()
        av = _avatar()
        snap = _snapshot(av)
        store.save(snap)
        assert store.load(av.id) == snap

    def test_returns_none_for_different_avatar_id(self) -> None:
        store = MemoryStore()
        av = _avatar()
        snap = _snapshot(av)
        store.save(snap)
        other_id = AvatarId(uuid4())
        assert store.load(other_id) is None


# ---------------------------------------------------------------------------
# MemoryStore.save
# ---------------------------------------------------------------------------


class TestMemoryStoreSave:
    def test_overwrites_existing_snapshot(self) -> None:
        store = MemoryStore()
        av = _avatar()
        snap1 = _snapshot(av)
        snap2 = GameSnapshot(
            avatar=av,
            room=Room(
                id=RoomId(uuid4()),
                avatar_id=av.id,
                level=1,
                applied_upgrades=("upgrade_x",),
            ),
            history=create_history(),
            sustained_since=100.0,
            last_tick=200.0,
        )
        store.save(snap1)
        store.save(snap2)
        assert store.load(av.id) == snap2

    def test_two_avatars_stored_independently(self) -> None:
        store = MemoryStore()
        av1 = _avatar()
        av2 = _avatar()
        snap1 = _snapshot(av1)
        snap2 = _snapshot(av2)
        store.save(snap1)
        store.save(snap2)
        assert store.load(av1.id) == snap1
        assert store.load(av2.id) == snap2
