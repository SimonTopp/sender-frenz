"""Tests for POST /level-up."""

from uuid import UUID, uuid4

from httpx import AsyncClient

from sender_frenz.api._helpers import make_snapshot
from sender_frenz.character_builder.catalog import SKIN_CATALOG
from sender_frenz.common.config import FAST_TEST_PACE
from sender_frenz.common.levels import (
    LevelConfig,
    room_options_for_level,
    skin_options_for_level,
)
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.persistence.store import MemoryStore
from sender_frenz.space_builder.catalog import ROOM_CATALOG

from .conftest import FIXED_NOW, VALID_HEADER, VALID_UUID

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LEVEL_CONFIG = LevelConfig.from_pace(FAST_TEST_PACE)

# A timestamp far enough in the past to satisfy the sustain window
_SUSTAINED_SINCE = FIXED_NOW - (_LEVEL_CONFIG.sustain_hours * 3600.0 + 1.0)


def _level_1_snapshot(avatar_id: AvatarId, store: MemoryStore) -> GameSnapshot:
    """Create and save a level-1 avatar with level-up available."""
    base = make_snapshot(avatar_id, FIXED_NOW)
    # Bump to level 1 by applying a valid level-up (requires a level-1 skin/room)
    # Instead, directly construct a level-1 avatar so we can pick valid slugs
    level_1_avatar = Avatar(
        id=avatar_id,
        needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=FIXED_NOW),
        social=SocialState(
            score=1.0,
            vampiric_stage=VampiricStage.NONE,
            last_interaction=FIXED_NOW,
        ),
        level=Level(current=1, skin_upgrades=(), room_upgrades=()),
        created_at=FIXED_NOW,
    )
    from sender_frenz.common.models import Room

    level_1_room = Room(
        id=base.room.id,
        avatar_id=avatar_id,
        level=1,
        applied_upgrades=(),
    )
    snap = GameSnapshot(
        avatar=level_1_avatar,
        room=level_1_room,
        history=base.history,
        sustained_since=_SUSTAINED_SINCE,
        last_tick=FIXED_NOW,
    )
    store.save(snap)
    return snap


def _eligible_snapshot(avatar_id: AvatarId, store: MemoryStore) -> GameSnapshot:
    """Create and save a level-0 avatar that qualifies for level-up."""
    base = make_snapshot(avatar_id, FIXED_NOW)
    snap = GameSnapshot(
        avatar=base.avatar,
        room=base.room,
        history=base.history,
        sustained_since=_SUSTAINED_SINCE,
        last_tick=FIXED_NOW,
    )
    store.save(snap)
    return snap


# ---------------------------------------------------------------------------
# 404 — unknown avatar
# ---------------------------------------------------------------------------


async def test_level_up_unknown_avatar_returns_409(client: AsyncClient):
    # Unknown avatar → make_snapshot → no sustained_since → 409
    uid = str(uuid4())
    response = await client.post(
        "/level-up",
        headers={"avatar-id": uid},
        json={"skin_slug": "torn-canvas", "room_slug": "archive-instance"},
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# 409 — not eligible
# ---------------------------------------------------------------------------


async def test_level_up_no_sustained_since_returns_409(
    client: AsyncClient,
    store: MemoryStore,
):
    aid = AvatarId(UUID(VALID_UUID))
    base = make_snapshot(aid, FIXED_NOW)
    store.save(base)  # sustained_since=None → not eligible
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": "torn-canvas", "room_slug": "archive-instance"},
    )
    assert response.status_code == 409


async def test_level_up_insufficient_time_returns_409(
    client: AsyncClient,
    store: MemoryStore,
):
    aid = AvatarId(UUID(VALID_UUID))
    base = make_snapshot(aid, FIXED_NOW)
    # sustained_since = now, so sustain window hasn't elapsed
    snap = GameSnapshot(
        avatar=base.avatar,
        room=base.room,
        history=base.history,
        sustained_since=FIXED_NOW,  # just now → not enough time
        last_tick=FIXED_NOW,
    )
    store.save(snap)
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": "torn-canvas", "room_slug": "archive-instance"},
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# 422 — invalid slugs
# ---------------------------------------------------------------------------


async def test_level_up_invalid_skin_slug_returns_422(
    client: AsyncClient,
    store: MemoryStore,
):
    aid = AvatarId(UUID(VALID_UUID))
    _eligible_snapshot(aid, store)
    # Level-0 avatar has no available skin options (tier >= 1 required)
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": "nonexistent-skin", "room_slug": "archive-instance"},
    )
    assert response.status_code == 422


async def test_level_up_missing_skin_slug_returns_422(
    client: AsyncClient, store: MemoryStore
):
    aid = AvatarId(UUID(VALID_UUID))
    _eligible_snapshot(aid, store)
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"room_slug": "archive-instance"},
    )
    assert response.status_code == 422


async def test_level_up_missing_room_slug_returns_422(
    client: AsyncClient, store: MemoryStore
):
    aid = AvatarId(UUID(VALID_UUID))
    _eligible_snapshot(aid, store)
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": "torn-canvas"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 200 — successful level-up
# ---------------------------------------------------------------------------


async def test_level_up_returns_200(client: AsyncClient, store: MemoryStore):
    aid = AvatarId(UUID(VALID_UUID))
    _level_1_snapshot(aid, store)
    skin_opts = skin_options_for_level(store.load(aid).avatar, SKIN_CATALOG)  # type: ignore[union-attr]
    room_opts = room_options_for_level(store.load(aid).room, ROOM_CATALOG)  # type: ignore[union-attr]
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": skin_opts[0].slug, "room_slug": room_opts[0].slug},
    )
    assert response.status_code == 200


async def test_level_up_increments_level_in_store(
    client: AsyncClient, store: MemoryStore
):
    aid = AvatarId(UUID(VALID_UUID))
    _level_1_snapshot(aid, store)
    snap = store.load(aid)
    assert snap is not None
    level_before = snap.avatar.level.current
    skin_opts = skin_options_for_level(snap.avatar, SKIN_CATALOG)
    room_opts = room_options_for_level(snap.room, ROOM_CATALOG)
    await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": skin_opts[0].slug, "room_slug": room_opts[0].slug},
    )
    snap_after = store.load(aid)
    assert snap_after is not None
    assert snap_after.avatar.level.current == level_before + 1


async def test_level_up_resets_sustained_since_in_store(
    client: AsyncClient, store: MemoryStore
):
    aid = AvatarId(UUID(VALID_UUID))
    _level_1_snapshot(aid, store)
    snap = store.load(aid)
    assert snap is not None
    skin_opts = skin_options_for_level(snap.avatar, SKIN_CATALOG)
    room_opts = room_options_for_level(snap.room, ROOM_CATALOG)
    await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": skin_opts[0].slug, "room_slug": room_opts[0].slug},
    )
    snap_after = store.load(aid)
    assert snap_after is not None
    assert snap_after.sustained_since is None


async def test_level_up_response_has_level(client: AsyncClient, store: MemoryStore):
    aid = AvatarId(UUID(VALID_UUID))
    _level_1_snapshot(aid, store)
    snap = store.load(aid)
    assert snap is not None
    skin_opts = skin_options_for_level(snap.avatar, SKIN_CATALOG)
    room_opts = room_options_for_level(snap.room, ROOM_CATALOG)
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": skin_opts[0].slug, "room_slug": room_opts[0].slug},
    )
    data = response.json()
    assert "level" in data
    assert data["level"]["current"] == snap.avatar.level.current + 1


async def test_level_up_response_has_skin_and_room_options(
    client: AsyncClient, store: MemoryStore
):
    aid = AvatarId(UUID(VALID_UUID))
    _level_1_snapshot(aid, store)
    snap = store.load(aid)
    assert snap is not None
    skin_opts = skin_options_for_level(snap.avatar, SKIN_CATALOG)
    room_opts = room_options_for_level(snap.room, ROOM_CATALOG)
    response = await client.post(
        "/level-up",
        headers=VALID_HEADER,
        json={"skin_slug": skin_opts[0].slug, "room_slug": room_opts[0].slug},
    )
    data = response.json()
    assert isinstance(data["skin_options"], list)
    assert isinstance(data["room_options"], list)


async def test_level_up_missing_header_returns_422(client: AsyncClient):
    response = await client.post(
        "/level-up",
        json={"skin_slug": "torn-canvas", "room_slug": "archive-instance"},
    )
    assert response.status_code == 422
