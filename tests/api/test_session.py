"""Tests for POST /session/open and GET /avatar/{id}."""

from uuid import UUID, uuid4

from httpx import AsyncClient

from sender_frenz.common.config import FAST_TEST_PACE
from sender_frenz.common.levels import LevelConfig, combined_health
from sender_frenz.common.types import AvatarId
from sender_frenz.persistence.store import MemoryStore

from .conftest import FIXED_NOW, VALID_HEADER, VALID_UUID

# ---------------------------------------------------------------------------
# POST /session/open
# ---------------------------------------------------------------------------


async def test_open_session_returns_200(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    assert response.status_code == 200


async def test_open_session_missing_header_returns_422(client: AsyncClient):
    response = await client.post("/session/open")
    assert response.status_code == 422


async def test_open_session_invalid_uuid_header_returns_422(client: AsyncClient):
    response = await client.post("/session/open", headers={"avatar-id": "not-a-uuid"})
    assert response.status_code == 422


async def test_open_session_response_has_avatar_id(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    assert data["avatar_id"] == VALID_UUID


async def test_open_session_response_has_quips(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    assert len(data["quips"]) >= 1


async def test_open_session_response_has_events_list(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    assert isinstance(data["events"], list)


async def test_open_session_fresh_avatar_level_up_not_available(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    assert data["level_up_available"] is False


async def test_open_session_saves_snapshot_to_store(
    client: AsyncClient, store: MemoryStore
):
    await client.post("/session/open", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    assert store.load(aid) is not None


async def test_open_session_snapshot_last_tick_equals_now(
    client: AsyncClient, store: MemoryStore
):
    await client.post("/session/open", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    snap = store.load(aid)
    assert snap is not None
    assert snap.last_tick == FIXED_NOW


async def test_open_session_sets_sustained_since_for_fresh_healthy_avatar(
    client: AsyncClient,
    store: MemoryStore,
):
    # Fresh avatar has full meters (1.0/1.0/1.0), combined health well above threshold
    await client.post("/session/open", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    snap = store.load(aid)
    assert snap is not None
    config = LevelConfig.from_pace(FAST_TEST_PACE)
    assert combined_health(snap.avatar) >= config.threshold
    assert snap.sustained_since == FIXED_NOW


async def test_open_session_response_needs_fields(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    needs = data["needs"]
    assert "hunger" in needs
    assert "hygiene" in needs


async def test_open_session_response_social_fields(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    social = data["social"]
    assert "score" in social
    assert "vampiric_stage" in social


async def test_open_session_response_appearance_fields(client: AsyncClient):
    response = await client.post("/session/open", headers=VALID_HEADER)
    data = response.json()
    appearance = data["appearance"]
    assert "vampiric_stage" in appearance
    assert "hunger_visual" in appearance
    assert "hygiene_visual" in appearance
    assert "composite_label" in appearance


async def test_open_session_idempotent_for_existing_avatar(
    client: AsyncClient,
    store: MemoryStore,
):
    # Two opens in sequence should both succeed and use the stored snapshot
    r1 = await client.post("/session/open", headers=VALID_HEADER)
    r2 = await client.post("/session/open", headers=VALID_HEADER)
    assert r1.status_code == 200
    assert r2.status_code == 200


# ---------------------------------------------------------------------------
# GET /avatar/avatar_id endpoint
# ---------------------------------------------------------------------------


async def test_get_avatar_returns_404_for_unknown(client: AsyncClient):
    uid = str(uuid4())
    response = await client.get(f"/avatar/{uid}")
    assert response.status_code == 404


async def test_get_avatar_returns_200_after_session_open(client: AsyncClient):
    await client.post("/session/open", headers=VALID_HEADER)
    response = await client.get(f"/avatar/{VALID_UUID}")
    assert response.status_code == 200


async def test_get_avatar_response_avatar_id(client: AsyncClient):
    await client.post("/session/open", headers=VALID_HEADER)
    response = await client.get(f"/avatar/{VALID_UUID}")
    assert response.json()["avatar_id"] == VALID_UUID


async def test_get_avatar_does_not_modify_store(
    client: AsyncClient, store: MemoryStore
):
    await client.post("/session/open", headers=VALID_HEADER)
    aid = AvatarId(UUID(VALID_UUID))
    snap_before = store.load(aid)
    await client.get(f"/avatar/{VALID_UUID}")
    snap_after = store.load(aid)
    assert snap_before == snap_after


async def test_get_avatar_returns_422_for_bad_uuid(client: AsyncClient):
    response = await client.get("/avatar/not-a-uuid")
    assert response.status_code == 422


async def test_get_avatar_response_has_last_tick(client: AsyncClient):
    await client.post("/session/open", headers=VALID_HEADER)
    response = await client.get(f"/avatar/{VALID_UUID}")
    data = response.json()
    assert data["last_tick"] == FIXED_NOW


async def test_get_avatar_response_has_sustained_since(client: AsyncClient):
    await client.post("/session/open", headers=VALID_HEADER)
    response = await client.get(f"/avatar/{VALID_UUID}")
    data = response.json()
    assert "sustained_since" in data
