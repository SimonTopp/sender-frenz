"""Tests for sender_frenz.common.levels."""

import dataclasses
from uuid import uuid4

import pytest

from sender_frenz.common.config import PRODUCTION_PACE, TEST_PACE, GamePace
from sender_frenz.common.levels import (
    LevelConfig,
    UpgradeOption,
    apply_level_up,
    combined_health,
    is_level_up_available,
    room_options_for_level,
    skin_options_for_level,
)
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    Room,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId, RoomId

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROD_CONFIG = LevelConfig.from_pace(PRODUCTION_PACE)
_ONE_HOUR = 3600.0


def _avatar(
    hunger: float = 1.0,
    hygiene: float = 1.0,
    score: float = 1.0,
    level: int = 0,
    skin_upgrades: tuple[str, ...] = (),
    room_upgrades: tuple[str, ...] = (),
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=0.0),
        social=SocialState(
            score=score,
            vampiric_stage=VampiricStage.NONE,
            last_interaction=0.0,
        ),
        level=Level(
            current=level,
            skin_upgrades=skin_upgrades,
            room_upgrades=room_upgrades,
        ),
        created_at=0.0,
    )


def _room(
    level: int = 0,
    applied_upgrades: tuple[str, ...] = (),
    avatar_id: AvatarId | None = None,
) -> Room:
    return Room(
        id=RoomId(uuid4()),
        avatar_id=avatar_id or AvatarId(uuid4()),
        level=level,
        applied_upgrades=applied_upgrades,
    )


def _opt(slug: str, tier: int = 0) -> UpgradeOption:
    return UpgradeOption(
        slug=slug,
        name="Test Option",
        tier=tier,
        description="A test upgrade option.",
    )


# ---------------------------------------------------------------------------
# LevelConfig.from_pace
# ---------------------------------------------------------------------------


class TestLevelConfigFromPace:
    def test_production_threshold(self) -> None:
        cfg = LevelConfig.from_pace(PRODUCTION_PACE)
        assert cfg.threshold == pytest.approx(0.75)

    def test_production_sustain_hours(self) -> None:
        cfg = LevelConfig.from_pace(PRODUCTION_PACE)
        assert cfg.sustain_hours == pytest.approx(4.0)

    def test_test_pace_compresses_sustain(self) -> None:
        cfg = LevelConfig.from_pace(TEST_PACE)
        assert cfg.sustain_hours == pytest.approx(4.0 / 720.0)

    def test_threshold_unchanged_by_pace(self) -> None:
        prod_cfg = LevelConfig.from_pace(PRODUCTION_PACE)
        test_cfg = LevelConfig.from_pace(TEST_PACE)
        assert prod_cfg.threshold == test_cfg.threshold

    def test_custom_pace(self) -> None:
        cfg = LevelConfig.from_pace(GamePace(time_scale=10.0))
        assert cfg.sustain_hours == pytest.approx(4.0 / 10.0)


# ---------------------------------------------------------------------------
# UpgradeOption
# ---------------------------------------------------------------------------


class TestUpgradeOption:
    def test_valid_construction(self) -> None:
        opt = _opt("torn-hoodie", tier=1)
        assert opt.slug == "torn-hoodie"
        assert opt.tier == 1

    def test_empty_slug_raises(self) -> None:
        with pytest.raises(ValueError, match="slug must not be empty"):
            UpgradeOption(slug="", name="X", tier=0, description="X")

    def test_negative_tier_raises(self) -> None:
        with pytest.raises(ValueError, match="tier must be >= 0"):
            UpgradeOption(slug="x", name="X", tier=-1, description="X")

    def test_frozen(self) -> None:
        opt = _opt("x")
        with pytest.raises(dataclasses.FrozenInstanceError):
            opt.slug = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# combined_health
# ---------------------------------------------------------------------------


class TestCombinedHealth:
    def test_all_full_returns_one(self) -> None:
        av = _avatar(hunger=1.0, hygiene=1.0, score=1.0)
        assert combined_health(av) == pytest.approx(1.0)

    def test_all_empty_returns_zero(self) -> None:
        av = _avatar(hunger=0.0, hygiene=0.0, score=0.0)
        assert combined_health(av) == pytest.approx(0.0)

    def test_average_of_three_meters(self) -> None:
        av = _avatar(hunger=0.9, hygiene=0.6, score=0.3)
        assert combined_health(av) == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# is_level_up_available
# ---------------------------------------------------------------------------


class TestIsLevelUpAvailable:
    def test_healthy_and_sustained_returns_true(self) -> None:
        av = _avatar(hunger=1.0, hygiene=1.0, score=1.0)
        # sustained_since=0, now = sustain_hours * 3600 + 1
        now = _PROD_CONFIG.sustain_hours * _ONE_HOUR + 1.0
        assert is_level_up_available(av, 0.0, now, _PROD_CONFIG)

    def test_below_threshold_returns_false(self) -> None:
        av = _avatar(hunger=0.5, hygiene=0.5, score=0.5)
        now = _PROD_CONFIG.sustain_hours * _ONE_HOUR + 1.0
        assert not is_level_up_available(av, 0.0, now, _PROD_CONFIG)

    def test_threshold_met_but_not_sustained_returns_false(self) -> None:
        av = _avatar(hunger=1.0, hygiene=1.0, score=1.0)
        # Only 1 second elapsed
        assert not is_level_up_available(av, 0.0, 1.0, _PROD_CONFIG)

    def test_exactly_at_threshold_score_qualifies(self) -> None:
        # threshold = 0.75; three equal meters at 0.75 → combined = 0.75
        av = _avatar(hunger=0.75, hygiene=0.75, score=0.75)
        now = _PROD_CONFIG.sustain_hours * _ONE_HOUR + 1.0
        assert is_level_up_available(av, 0.0, now, _PROD_CONFIG)

    def test_just_below_threshold_score_does_not_qualify(self) -> None:
        av = _avatar(hunger=0.74, hygiene=0.75, score=0.75)
        now = _PROD_CONFIG.sustain_hours * _ONE_HOUR + 1.0
        assert not is_level_up_available(av, 0.0, now, _PROD_CONFIG)


# ---------------------------------------------------------------------------
# skin_options_for_level / room_options_for_level
# ---------------------------------------------------------------------------


class TestSkinOptionsForLevel:
    def test_returns_options_at_or_below_level(self) -> None:
        catalog = [_opt("a", tier=0), _opt("b", tier=1), _opt("c", tier=2)]
        av = _avatar(level=1)
        opts = skin_options_for_level(av, catalog)
        assert {o.slug for o in opts} == {"a", "b"}

    def test_excludes_already_applied(self) -> None:
        catalog = [_opt("a", tier=0), _opt("b", tier=0)]
        av = _avatar(level=0, skin_upgrades=("a",))
        opts = skin_options_for_level(av, catalog)
        assert {o.slug for o in opts} == {"b"}

    def test_empty_catalog_returns_empty(self) -> None:
        av = _avatar(level=5)
        assert skin_options_for_level(av, []) == ()


class TestRoomOptionsForLevel:
    def test_returns_options_at_or_below_level(self) -> None:
        catalog = [_opt("x", tier=0), _opt("y", tier=2)]
        room = _room(level=1)
        opts = room_options_for_level(room, catalog)
        assert {o.slug for o in opts} == {"x"}

    def test_excludes_already_applied(self) -> None:
        catalog = [_opt("x", tier=0), _opt("y", tier=0)]
        room = _room(level=0, applied_upgrades=("x",))
        opts = room_options_for_level(room, catalog)
        assert {o.slug for o in opts} == {"y"}


# ---------------------------------------------------------------------------
# apply_level_up
# ---------------------------------------------------------------------------


class TestApplyLevelUp:
    def _setup(self) -> tuple[Avatar, Room, list[UpgradeOption], list[UpgradeOption]]:
        av = _avatar(level=0)
        room = _room(level=0, avatar_id=av.id)
        skin_catalog = [_opt("torn-hoodie", tier=0), _opt("cracked-goggles", tier=0)]
        room_catalog = [_opt("pixel-graffiti", tier=0), _opt("crt-monitor", tier=0)]
        return av, room, skin_catalog, room_catalog

    def test_increments_avatar_level(self) -> None:
        av, room, sk, rm = self._setup()
        new_av, _ = apply_level_up(av, room, "torn-hoodie", "pixel-graffiti", sk, rm)
        assert new_av.level.current == 1

    def test_increments_room_level(self) -> None:
        av, room, sk, rm = self._setup()
        _, new_room = apply_level_up(av, room, "torn-hoodie", "pixel-graffiti", sk, rm)
        assert new_room.level == 1

    def test_records_skin_upgrade_slug(self) -> None:
        av, room, sk, rm = self._setup()
        new_av, _ = apply_level_up(av, room, "torn-hoodie", "pixel-graffiti", sk, rm)
        assert "torn-hoodie" in new_av.level.skin_upgrades

    def test_records_room_upgrade_slug(self) -> None:
        av, room, sk, rm = self._setup()
        _, new_room = apply_level_up(av, room, "torn-hoodie", "pixel-graffiti", sk, rm)
        assert "pixel-graffiti" in new_room.applied_upgrades

    def test_preserves_avatar_id_and_stats(self) -> None:
        av, room, sk, rm = self._setup()
        new_av, _ = apply_level_up(av, room, "torn-hoodie", "pixel-graffiti", sk, rm)
        assert new_av.id == av.id
        assert new_av.needs == av.needs
        assert new_av.social == av.social

    def test_invalid_skin_slug_raises(self) -> None:
        av, room, sk, rm = self._setup()
        with pytest.raises(ValueError, match="skin slug"):
            apply_level_up(av, room, "nonexistent-skin", "pixel-graffiti", sk, rm)

    def test_invalid_room_slug_raises(self) -> None:
        av, room, sk, rm = self._setup()
        with pytest.raises(ValueError, match="room slug"):
            apply_level_up(av, room, "torn-hoodie", "nonexistent-room", sk, rm)

    def test_already_applied_skin_slug_raises(self) -> None:
        av = _avatar(level=0, skin_upgrades=("torn-hoodie",))
        room = _room(level=0, avatar_id=av.id)
        skin_catalog = [_opt("torn-hoodie", tier=0)]
        room_catalog = [_opt("pixel-graffiti", tier=0)]
        with pytest.raises(ValueError, match="skin slug"):
            apply_level_up(
                av, room, "torn-hoodie", "pixel-graffiti", skin_catalog, room_catalog
            )

    def test_already_applied_room_slug_raises(self) -> None:
        av = _avatar(level=0)
        room = _room(level=0, avatar_id=av.id, applied_upgrades=("pixel-graffiti",))
        skin_catalog = [_opt("torn-hoodie", tier=0)]
        room_catalog = [_opt("pixel-graffiti", tier=0)]
        with pytest.raises(ValueError, match="room slug"):
            apply_level_up(
                av, room, "torn-hoodie", "pixel-graffiti", skin_catalog, room_catalog
            )

    def test_returns_new_instances(self) -> None:
        av, room, sk, rm = self._setup()
        new_av, new_room = apply_level_up(
            av, room, "torn-hoodie", "pixel-graffiti", sk, rm
        )
        assert new_av is not av
        assert new_room is not room
