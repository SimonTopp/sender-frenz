"""Tests for sender_frenz.common.models."""

import dataclasses
from uuid import uuid4

import pytest

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    Room,
    SocialState,
    VampiricStage,
    vampiric_stage_from_index,
    vampiric_stage_index,
)
from sender_frenz.common.types import AvatarId, RoomId

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _avatar_id() -> AvatarId:
    return AvatarId(uuid4())


def _room_id() -> RoomId:
    return RoomId(uuid4())


def _need_state(hunger: float = 1.0, hygiene: float = 1.0) -> NeedState:
    return NeedState(hunger=hunger, hygiene=hygiene, last_updated=0.0)


def _social_state(score: float = 1.0) -> SocialState:
    return SocialState(
        score=score,
        vampiric_stage=VampiricStage.NONE,
        last_interaction=0.0,
    )


def _level() -> Level:
    return Level(current=0, skin_upgrades=(), room_upgrades=())


def _avatar() -> Avatar:
    return Avatar(
        id=_avatar_id(),
        needs=_need_state(),
        social=_social_state(),
        level=_level(),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# VampiricStage
# ---------------------------------------------------------------------------


class TestVampiricStageIndex:
    def test_none_is_zero(self) -> None:
        assert vampiric_stage_index(VampiricStage.NONE) == 0

    def test_vampiric_is_four(self) -> None:
        assert vampiric_stage_index(VampiricStage.VAMPIRIC) == 4

    def test_all_stages_unique(self) -> None:
        indices = [vampiric_stage_index(s) for s in VampiricStage]
        assert len(set(indices)) == len(indices)


class TestVampiricStageFromIndex:
    def test_zero_returns_none(self) -> None:
        assert vampiric_stage_from_index(0) == VampiricStage.NONE

    def test_four_returns_vampiric(self) -> None:
        assert vampiric_stage_from_index(4) == VampiricStage.VAMPIRIC

    def test_negative_clamps_to_none(self) -> None:
        assert vampiric_stage_from_index(-99) == VampiricStage.NONE

    def test_overflow_clamps_to_vampiric(self) -> None:
        assert vampiric_stage_from_index(999) == VampiricStage.VAMPIRIC

    def test_roundtrip(self) -> None:
        for stage in VampiricStage:
            assert vampiric_stage_from_index(vampiric_stage_index(stage)) == stage


# ---------------------------------------------------------------------------
# NeedState
# ---------------------------------------------------------------------------


class TestNeedState:
    def test_valid_construction(self) -> None:
        ns = NeedState(hunger=0.5, hygiene=0.8, last_updated=100.0)
        assert ns.hunger == 0.5
        assert ns.hygiene == 0.8
        assert ns.last_updated == 100.0

    def test_boundary_values_accepted(self) -> None:
        NeedState(hunger=0.0, hygiene=0.0, last_updated=0.0)
        NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0)

    def test_hunger_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="hunger"):
            NeedState(hunger=1.1, hygiene=1.0, last_updated=0.0)

    def test_hunger_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="hunger"):
            NeedState(hunger=-0.1, hygiene=1.0, last_updated=0.0)

    def test_hygiene_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="hygiene"):
            NeedState(hunger=1.0, hygiene=1.1, last_updated=0.0)

    def test_frozen(self) -> None:
        ns = _need_state()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ns.hunger = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SocialState
# ---------------------------------------------------------------------------


class TestSocialState:
    def test_valid_construction(self) -> None:
        ss = SocialState(
            score=0.5,
            vampiric_stage=VampiricStage.PALLOR,
            last_interaction=50.0,
        )
        assert ss.score == 0.5
        assert ss.vampiric_stage == VampiricStage.PALLOR

    def test_score_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="score"):
            SocialState(
                score=1.1,
                vampiric_stage=VampiricStage.NONE,
                last_interaction=0.0,
            )

    def test_score_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="score"):
            SocialState(
                score=-0.1,
                vampiric_stage=VampiricStage.NONE,
                last_interaction=0.0,
            )

    def test_frozen(self) -> None:
        ss = _social_state()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ss.score = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------


class TestLevel:
    def test_valid_construction(self) -> None:
        lv = Level(current=3, skin_upgrades=("a",), room_upgrades=("b",))
        assert lv.current == 3

    def test_zero_level_accepted(self) -> None:
        Level(current=0, skin_upgrades=(), room_upgrades=())

    def test_negative_level_raises(self) -> None:
        with pytest.raises(ValueError, match="current level"):
            Level(current=-1, skin_upgrades=(), room_upgrades=())

    def test_frozen(self) -> None:
        lv = _level()
        with pytest.raises(dataclasses.FrozenInstanceError):
            lv.current = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------


class TestAvatar:
    def test_valid_construction(self) -> None:
        av = _avatar()
        assert av.created_at == 0.0

    def test_frozen(self) -> None:
        av = _avatar()
        with pytest.raises(dataclasses.FrozenInstanceError):
            av.created_at = 999.0  # type: ignore[misc]

    def test_unique_ids(self) -> None:
        a1 = _avatar()
        a2 = _avatar()
        assert a1.id != a2.id


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------


class TestRoom:
    def test_valid_construction(self) -> None:
        room = Room(
            id=_room_id(),
            avatar_id=_avatar_id(),
            level=0,
            applied_upgrades=(),
        )
        assert room.level == 0

    def test_negative_level_raises(self) -> None:
        with pytest.raises(ValueError, match="room level"):
            Room(
                id=_room_id(),
                avatar_id=_avatar_id(),
                level=-1,
                applied_upgrades=(),
            )

    def test_frozen(self) -> None:
        room = Room(
            id=_room_id(),
            avatar_id=_avatar_id(),
            level=0,
            applied_upgrades=(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            room.level = 5  # type: ignore[misc]
