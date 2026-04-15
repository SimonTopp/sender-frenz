"""Tests for POST /action/{kind}."""

from uuid import UUID, uuid4

from httpx import AsyncClient

from sender_frenz.common.types import AvatarId
from sender_frenz.persistence.store import MemoryStore

from .conftest import FIXED_NOW, VALID_HEADER, VALID_UUID

# ---------------------------------------------------------------------------
# Unknown action kind
# ---------------------------------------------------------------------------


async def test_unknown_kind_returns_422(client: AsyncClient):
    response = await client.post("/action/sleep", headers=VALID_HEADER)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# All five valid kinds return 200
# ---------------------------------------------------------------------------


async def test_feed_returns_200(client: AsyncClient):
    response = await client.post("/action/feed", headers=VALID_HEADER)
    assert response.status_code == 200


async def test_clean_returns_200(client: AsyncClient):
    response = await client.post("/action/clean", headers=VALID_HEADER)
    assert response.status_code == 200


async def test_visit_returns_200(client: AsyncClient):
    response = await client.post("/action/visit", headers=VALID_HEADER)
    assert response.status_code == 200


async def test_gift_returns_200(client: AsyncClient):
    response = await client.post("/action/gift", headers=VALID_HEADER)
    assert response.status_code == 200


async def test_chat_returns_200(client: AsyncClient):
    response = await client.post("/action/chat", headers=VALID_HEADER)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


async def test_action_response_has_quip(client: AsyncClient):
    response = await client.post("/action/feed", headers=VALID_HEADER)
    data = response.json()
    assert isinstance(data["quip"], str)
    assert len(data["quip"]) > 0


async def test_action_response_has_avatar_id(client: AsyncClient):
    response = await client.post("/action/feed", headers=VALID_HEADER)
    data = response.json()
    assert data["avatar_id"] == VALID_UUID


async def test_action_response_has_needs(client: AsyncClient):
    response = await client.post("/action/feed", headers=VALID_HEADER)
    data = response.json()
    assert "hunger" in data["needs"]
    assert "hygiene" in data["needs"]


async def test_action_response_has_social(client: AsyncClient):
    response = await client.post("/action/visit", headers=VALID_HEADER)
    data = response.json()
    assert "score" in data["social"]
    assert "vampiric_stage" in data["social"]


# ---------------------------------------------------------------------------
# Store mutations
# ---------------------------------------------------------------------------


async def test_feed_saves_to_store(client: AsyncClient, store: MemoryStore):
    await client.post("/action/feed", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    assert store.load(aid) is not None


async def test_feed_increases_hunger_in_store(client: AsyncClient, store: MemoryStore):
    from sender_frenz.api._helpers import make_snapshot
    from sender_frenz.common.models import (
        Avatar,
        NeedState,
        SocialState,
        VampiricStage,
    )
    from sender_frenz.persistence.snapshots import GameSnapshot

    aid = AvatarId(UUID(VALID_UUID))
    base = make_snapshot(aid, FIXED_NOW)
    # Start with depleted hunger so feed has room to increase it
    depleted_avatar = Avatar(
        id=aid,
        needs=NeedState(hunger=0.3, hygiene=1.0, last_updated=FIXED_NOW),
        social=SocialState(
            score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=FIXED_NOW
        ),
        level=base.avatar.level,
        created_at=base.avatar.created_at,
    )
    store.save(
        GameSnapshot(
            avatar=depleted_avatar,
            room=base.room,
            history=base.history,
            sustained_since=base.sustained_since,
            last_tick=base.last_tick,
        )
    )
    await client.post("/action/feed", headers=VALID_HEADER)
    snap_after = store.load(aid)
    assert snap_after is not None
    assert snap_after.avatar.needs.hunger > 0.3


async def test_clean_increases_hygiene_in_store(
    client: AsyncClient, store: MemoryStore
):
    from sender_frenz.api._helpers import make_snapshot
    from sender_frenz.common.models import (
        Avatar,
        NeedState,
        SocialState,
        VampiricStage,
    )
    from sender_frenz.persistence.snapshots import GameSnapshot

    aid = AvatarId(UUID(VALID_UUID))
    base = make_snapshot(aid, FIXED_NOW)
    depleted_avatar = Avatar(
        id=aid,
        needs=NeedState(hunger=1.0, hygiene=0.2, last_updated=FIXED_NOW),
        social=SocialState(
            score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=FIXED_NOW
        ),
        level=base.avatar.level,
        created_at=base.avatar.created_at,
    )
    store.save(
        GameSnapshot(
            avatar=depleted_avatar,
            room=base.room,
            history=base.history,
            sustained_since=base.sustained_since,
            last_tick=base.last_tick,
        )
    )
    await client.post("/action/clean", headers=VALID_HEADER)
    snap_after = store.load(aid)
    assert snap_after is not None
    assert snap_after.avatar.needs.hygiene > 0.2


async def test_visit_increases_social_score_in_store(
    client: AsyncClient, store: MemoryStore
):
    # Deplete social score first by creating a custom snapshot
    from sender_frenz.api._helpers import make_snapshot
    from sender_frenz.common.models import (
        Avatar,
        SocialState,
        VampiricStage,
    )
    from sender_frenz.persistence.snapshots import GameSnapshot

    aid = AvatarId(UUID(VALID_UUID))
    base = make_snapshot(aid, FIXED_NOW)
    low_social_avatar = Avatar(
        id=aid,
        needs=base.avatar.needs,
        social=SocialState(
            score=0.3,
            vampiric_stage=VampiricStage.NONE,
            last_interaction=FIXED_NOW,
        ),
        level=base.avatar.level,
        created_at=base.avatar.created_at,
    )
    store.save(
        GameSnapshot(
            avatar=low_social_avatar,
            room=base.room,
            history=base.history,
            sustained_since=base.sustained_since,
            last_tick=base.last_tick,
        )
    )

    await client.post("/action/visit", headers=VALID_HEADER)
    snap_after = store.load(aid)
    assert snap_after is not None
    assert snap_after.avatar.social.score > 0.3


# ---------------------------------------------------------------------------
# sustained_since updates
# ---------------------------------------------------------------------------


async def test_action_on_unknown_avatar_bootstraps(
    client: AsyncClient, store: MemoryStore
):
    # No prior session open — action should auto-create and succeed
    uid = str(uuid4())
    response = await client.post("/action/feed", headers={"avatar-id": uid})
    assert response.status_code == 200


async def test_action_missing_header_returns_422(client: AsyncClient):
    response = await client.post("/action/feed")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# History updated for social interactions
# ---------------------------------------------------------------------------


async def test_social_action_updates_history(client: AsyncClient, store: MemoryStore):
    await client.post("/action/visit", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    snap = store.load(aid)
    assert snap is not None
    assert len(snap.history.events) == 1


async def test_maintenance_action_does_not_update_history(
    client: AsyncClient, store: MemoryStore
):
    await client.post("/action/feed", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    snap = store.load(aid)
    assert snap is not None
    assert len(snap.history.events) == 0
