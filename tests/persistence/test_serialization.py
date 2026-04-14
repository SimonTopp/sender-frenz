"""Tests for sender_frenz.persistence.serialization."""

import json
from uuid import UUID, uuid4

import pytest

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    Room,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId, RoomId
from sender_frenz.persistence.serialization import (
    _SNAPSHOT_VERSION,
    avatar_from_dict,
    avatar_to_dict,
    history_from_dict,
    history_to_dict,
    room_from_dict,
    room_to_dict,
    snapshot_from_dict,
    snapshot_from_json,
    snapshot_to_dict,
    snapshot_to_json,
)
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.social_maintenance.history import (
    InteractionHistory,
    add_event,
    create_history,
)
from sender_frenz.social_maintenance.interactions import InteractionKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _avatar(
    hunger: float = 1.0,
    hygiene: float = 1.0,
    social: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
    skin_upgrades: tuple[str, ...] = (),
    room_upgrades: tuple[str, ...] = (),
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=100.0),
        social=SocialState(score=social, vampiric_stage=stage, last_interaction=200.0),
        level=Level(
            current=2, skin_upgrades=skin_upgrades, room_upgrades=room_upgrades
        ),
        created_at=50.0,
    )


def _room(avatar_id: AvatarId | None = None) -> Room:
    if avatar_id is None:
        avatar_id = AvatarId(uuid4())
    return Room(
        id=RoomId(uuid4()),
        avatar_id=avatar_id,
        level=2,
        applied_upgrades=("upgrade_a", "upgrade_b"),
    )


def _snapshot(
    sustained_since: float | None = None, last_tick: float = 500.0
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
# avatar_to_dict
# ---------------------------------------------------------------------------


class TestAvatarToDict:
    def test_returns_dict(self) -> None:
        d = avatar_to_dict(_avatar())
        assert isinstance(d, dict)

    def test_has_id_key(self) -> None:
        av = _avatar()
        d = avatar_to_dict(av)
        assert "id" in d

    def test_id_is_string(self) -> None:
        d = avatar_to_dict(_avatar())
        assert isinstance(d["id"], str)

    def test_id_is_valid_uuid_string(self) -> None:
        av = _avatar()
        d = avatar_to_dict(av)
        assert UUID(d["id"]) == av.id

    def test_needs_sub_dict(self) -> None:
        d = avatar_to_dict(_avatar(hunger=0.8, hygiene=0.7))
        assert d["needs"]["hunger"] == pytest.approx(0.8)
        assert d["needs"]["hygiene"] == pytest.approx(0.7)
        assert d["needs"]["last_updated"] == pytest.approx(100.0)

    def test_social_score(self) -> None:
        d = avatar_to_dict(_avatar(social=0.6))
        assert d["social"]["score"] == pytest.approx(0.6)

    def test_vampiric_stage_stored_by_name(self) -> None:
        for stage in VampiricStage:
            d = avatar_to_dict(_avatar(stage=stage))
            assert d["social"]["vampiric_stage"] == stage.name

    def test_social_last_interaction(self) -> None:
        d = avatar_to_dict(_avatar())
        assert d["social"]["last_interaction"] == pytest.approx(200.0)

    def test_level_current(self) -> None:
        d = avatar_to_dict(_avatar())
        assert d["level"]["current"] == 2

    def test_skin_upgrades_is_list(self) -> None:
        av = _avatar(skin_upgrades=("a", "b"))
        d = avatar_to_dict(av)
        assert d["level"]["skin_upgrades"] == ["a", "b"]

    def test_room_upgrades_is_list(self) -> None:
        av = _avatar(room_upgrades=("x",))
        d = avatar_to_dict(av)
        assert d["level"]["room_upgrades"] == ["x"]

    def test_created_at(self) -> None:
        d = avatar_to_dict(_avatar())
        assert d["created_at"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# avatar_from_dict / round-trip
# ---------------------------------------------------------------------------


class TestAvatarRoundTrip:
    def test_round_trip(self) -> None:
        av = _avatar()
        assert avatar_from_dict(avatar_to_dict(av)) == av

    def test_uuid_round_trip(self) -> None:
        av = _avatar()
        result = avatar_from_dict(avatar_to_dict(av))
        assert result.id == av.id

    def test_skin_upgrades_round_trip_as_tuple(self) -> None:
        av = _avatar(skin_upgrades=("a", "b", "c"))
        result = avatar_from_dict(avatar_to_dict(av))
        assert isinstance(result.level.skin_upgrades, tuple)
        assert result.level.skin_upgrades == ("a", "b", "c")

    def test_room_upgrades_round_trip_as_tuple(self) -> None:
        av = _avatar(room_upgrades=("x", "y"))
        result = avatar_from_dict(avatar_to_dict(av))
        assert isinstance(result.level.room_upgrades, tuple)
        assert result.level.room_upgrades == ("x", "y")

    def test_all_vampiric_stages_round_trip(self) -> None:
        for stage in VampiricStage:
            av = _avatar(stage=stage)
            result = avatar_from_dict(avatar_to_dict(av))
            assert result.social.vampiric_stage is stage

    def test_empty_upgrades_round_trip(self) -> None:
        av = _avatar(skin_upgrades=(), room_upgrades=())
        result = avatar_from_dict(avatar_to_dict(av))
        assert result.level.skin_upgrades == ()
        assert result.level.room_upgrades == ()


# ---------------------------------------------------------------------------
# room_to_dict / room_from_dict / round-trip
# ---------------------------------------------------------------------------


class TestRoomRoundTrip:
    def test_room_to_dict_keys(self) -> None:
        d = room_to_dict(_room())
        for key in ("id", "avatar_id", "level", "applied_upgrades"):
            assert key in d

    def test_room_ids_are_strings(self) -> None:
        r = _room()
        d = room_to_dict(r)
        assert isinstance(d["id"], str)
        assert isinstance(d["avatar_id"], str)

    def test_applied_upgrades_is_list(self) -> None:
        d = room_to_dict(_room())
        assert isinstance(d["applied_upgrades"], list)

    def test_round_trip(self) -> None:
        r = _room()
        assert room_from_dict(room_to_dict(r)) == r

    def test_applied_upgrades_round_trip_as_tuple(self) -> None:
        r = _room()
        result = room_from_dict(room_to_dict(r))
        assert isinstance(result.applied_upgrades, tuple)
        assert result.applied_upgrades == r.applied_upgrades

    def test_empty_applied_upgrades_round_trip(self) -> None:
        av_id = AvatarId(uuid4())
        r = Room(id=RoomId(uuid4()), avatar_id=av_id, level=0, applied_upgrades=())
        result = room_from_dict(room_to_dict(r))
        assert result.applied_upgrades == ()


# ---------------------------------------------------------------------------
# history_to_dict / history_from_dict / round-trip
# ---------------------------------------------------------------------------


class TestHistoryRoundTrip:
    def test_empty_history_round_trips(self) -> None:
        h = create_history()
        result = history_from_dict(history_to_dict(h))
        assert result == h

    def test_empty_history_events_list(self) -> None:
        d = history_to_dict(create_history())
        assert d["events"] == []

    def test_single_event_round_trip(self) -> None:
        h = add_event(create_history(), InteractionKind.VISIT, 100.0)
        result = history_from_dict(history_to_dict(h))
        assert result == h

    def test_kind_stored_by_value(self) -> None:
        h = add_event(create_history(), InteractionKind.VISIT, 100.0)
        d = history_to_dict(h)
        assert d["events"][0]["kind"] == "visit"

    def test_gift_kind_stored_by_value(self) -> None:
        h = add_event(create_history(), InteractionKind.GIFT, 100.0)
        d = history_to_dict(h)
        assert d["events"][0]["kind"] == "gift"

    def test_chat_kind_stored_by_value(self) -> None:
        h = add_event(create_history(), InteractionKind.CHAT, 100.0)
        d = history_to_dict(h)
        assert d["events"][0]["kind"] == "chat"

    def test_mixed_kinds_round_trip(self) -> None:
        h = create_history()
        h = add_event(h, InteractionKind.CHAT, 100.0)
        h = add_event(h, InteractionKind.GIFT, 200.0)
        h = add_event(h, InteractionKind.VISIT, 300.0)
        result = history_from_dict(history_to_dict(h))
        assert result == h

    def test_newest_first_order_preserved(self) -> None:
        h = create_history()
        h = add_event(h, InteractionKind.CHAT, 100.0)
        h = add_event(h, InteractionKind.VISIT, 300.0)
        result = history_from_dict(history_to_dict(h))
        assert result.events[0].timestamp == pytest.approx(300.0)
        assert result.events[1].timestamp == pytest.approx(100.0)

    def test_result_is_interaction_history(self) -> None:
        h = create_history()
        result = history_from_dict(history_to_dict(h))
        assert isinstance(result, InteractionHistory)


# ---------------------------------------------------------------------------
# snapshot_to_dict / snapshot_from_dict / round-trip
# ---------------------------------------------------------------------------


class TestSnapshotToDict:
    def test_version_key_present(self) -> None:
        d = snapshot_to_dict(_snapshot())
        assert "version" in d

    def test_version_equals_snapshot_version(self) -> None:
        d = snapshot_to_dict(_snapshot())
        assert d["version"] == _SNAPSHOT_VERSION

    def test_has_avatar_key(self) -> None:
        d = snapshot_to_dict(_snapshot())
        assert "avatar" in d

    def test_has_room_key(self) -> None:
        d = snapshot_to_dict(_snapshot())
        assert "room" in d

    def test_has_history_key(self) -> None:
        d = snapshot_to_dict(_snapshot())
        assert "history" in d

    def test_sustained_since_none(self) -> None:
        d = snapshot_to_dict(_snapshot(sustained_since=None))
        assert d["sustained_since"] is None

    def test_sustained_since_float(self) -> None:
        d = snapshot_to_dict(_snapshot(sustained_since=12345.6))
        assert d["sustained_since"] == pytest.approx(12345.6)

    def test_last_tick_stored(self) -> None:
        d = snapshot_to_dict(_snapshot(last_tick=999.0))
        assert d["last_tick"] == pytest.approx(999.0)


class TestSnapshotRoundTrip:
    def test_full_round_trip(self) -> None:
        s = _snapshot()
        assert snapshot_from_dict(snapshot_to_dict(s)) == s

    def test_sustained_since_none_round_trips(self) -> None:
        s = _snapshot(sustained_since=None)
        result = snapshot_from_dict(snapshot_to_dict(s))
        assert result.sustained_since is None

    def test_sustained_since_float_round_trips(self) -> None:
        s = _snapshot(sustained_since=42.0)
        result = snapshot_from_dict(snapshot_to_dict(s))
        assert result.sustained_since == pytest.approx(42.0)

    def test_raises_value_error_on_unknown_version(self) -> None:
        d = snapshot_to_dict(_snapshot())
        d["version"] = 999
        with pytest.raises(ValueError, match="999"):
            snapshot_from_dict(d)

    def test_raises_value_error_on_none_version(self) -> None:
        d = snapshot_to_dict(_snapshot())
        d["version"] = None
        with pytest.raises(ValueError, match="None"):
            snapshot_from_dict(d)


# ---------------------------------------------------------------------------
# JSON convenience
# ---------------------------------------------------------------------------


class TestSnapshotJson:
    def test_to_json_returns_string(self) -> None:
        assert isinstance(snapshot_to_json(_snapshot()), str)

    def test_to_json_is_valid_json(self) -> None:
        raw = snapshot_to_json(_snapshot())
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_json_round_trip(self) -> None:
        s = _snapshot()
        assert snapshot_from_json(snapshot_to_json(s)) == s

    def test_json_round_trip_with_sustained_since(self) -> None:
        s = _snapshot(sustained_since=77.0)
        result = snapshot_from_json(snapshot_to_json(s))
        assert result.sustained_since == pytest.approx(77.0)
