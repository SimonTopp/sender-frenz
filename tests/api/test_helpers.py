"""Tests for sender_frenz.api._helpers."""

from uuid import UUID, uuid4

from sender_frenz.api._helpers import make_snapshot, update_sustained_since
from sender_frenz.character_builder.avatar import create_avatar
from sender_frenz.common.config import FAST_TEST_PACE, PRODUCTION_PACE
from sender_frenz.common.levels import LevelConfig, combined_health
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId
from sender_frenz.persistence.snapshots import GameSnapshot

NOW = 1_000_000.0
AVATAR_ID = AvatarId(UUID("12345678-1234-5678-1234-567812345678"))


def _low_health_avatar(avatar_id: AvatarId) -> Avatar:
    return Avatar(
        id=avatar_id,
        needs=NeedState(hunger=0.1, hygiene=0.1, last_updated=NOW),
        social=SocialState(
            score=0.1, vampiric_stage=VampiricStage.NONE, last_interaction=NOW
        ),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=NOW,
    )


def _high_health_avatar(avatar_id: AvatarId) -> Avatar:
    return create_avatar(avatar_id, NOW)  # 1.0/1.0/1.0 — combined = 1.0


# ---------------------------------------------------------------------------
# update_sustained_since
# ---------------------------------------------------------------------------


def test_update_sustained_since_sets_now_when_none_and_above_threshold():
    avatar = _high_health_avatar(AVATAR_ID)
    assert combined_health(avatar) >= LevelConfig.from_pace(PRODUCTION_PACE).threshold
    result = update_sustained_since(avatar, None, NOW, PRODUCTION_PACE)
    assert result == NOW


def test_update_sustained_since_carries_forward_when_already_set():
    avatar = _high_health_avatar(AVATAR_ID)
    earlier = NOW - 3600.0
    result = update_sustained_since(avatar, earlier, NOW, PRODUCTION_PACE)
    assert result == earlier


def test_update_sustained_since_returns_none_when_below_threshold():
    avatar = _low_health_avatar(AVATAR_ID)
    assert combined_health(avatar) < LevelConfig.from_pace(PRODUCTION_PACE).threshold
    result = update_sustained_since(avatar, NOW - 1000.0, NOW, PRODUCTION_PACE)
    assert result is None


def test_update_sustained_since_returns_none_for_none_below_threshold():
    avatar = _low_health_avatar(AVATAR_ID)
    result = update_sustained_since(avatar, None, NOW, PRODUCTION_PACE)
    assert result is None


def test_update_sustained_since_uses_pace_for_threshold():
    # FAST_TEST_PACE has the same threshold as PRODUCTION_PACE (0.75)
    avatar = _high_health_avatar(AVATAR_ID)
    result = update_sustained_since(avatar, None, NOW, FAST_TEST_PACE)
    assert result == NOW


# ---------------------------------------------------------------------------
# make_snapshot
# ---------------------------------------------------------------------------


def test_make_snapshot_returns_game_snapshot():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert isinstance(snap, GameSnapshot)


def test_make_snapshot_avatar_id_matches():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.avatar.id == AVATAR_ID


def test_make_snapshot_room_avatar_id_matches():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.room.avatar_id == AVATAR_ID


def test_make_snapshot_room_id_is_different_from_avatar_id():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.room.id != snap.avatar.id


def test_make_snapshot_last_tick_is_now():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.last_tick == NOW


def test_make_snapshot_sustained_since_is_none():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.sustained_since is None


def test_make_snapshot_history_is_empty():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.history.events == ()


def test_make_snapshot_avatars_have_full_meters():
    snap = make_snapshot(AVATAR_ID, NOW)
    assert snap.avatar.needs.hunger == 1.0
    assert snap.avatar.needs.hygiene == 1.0
    assert snap.avatar.social.score == 1.0


def test_make_snapshot_can_be_saved_to_store():
    from sender_frenz.persistence.store import MemoryStore

    store = MemoryStore()
    snap = make_snapshot(AVATAR_ID, NOW)
    store.save(snap)
    loaded = store.load(AVATAR_ID)
    assert loaded is not None
    assert loaded.avatar.id == AVATAR_ID


def test_make_snapshot_different_avatar_ids_produce_different_snapshots():
    id1 = AvatarId(uuid4())
    id2 = AvatarId(uuid4())
    s1 = make_snapshot(id1, NOW)
    s2 = make_snapshot(id2, NOW)
    assert s1.avatar.id != s2.avatar.id
    assert s1.room.id != s2.room.id
