"""Tests for sender_frenz.space_builder.catalog."""

import pytest

from sender_frenz.common.levels import UpgradeOption
from sender_frenz.space_builder.catalog import (
    _TIER_1_MIN_LEVEL,
    _TIER_2_MIN_LEVEL,
    _TIER_3_MIN_LEVEL,
    _TIER_4_MIN_LEVEL,
    ROOM_CATALOG,
    rooms_for_level,
)

# ---------------------------------------------------------------------------
# ROOM_CATALOG structure
# ---------------------------------------------------------------------------


class TestRoomCatalogStructure:
    def test_catalog_is_not_empty(self) -> None:
        assert len(ROOM_CATALOG) > 0

    def test_all_entries_are_upgrade_options(self) -> None:
        for entry in ROOM_CATALOG:
            assert isinstance(entry, UpgradeOption)

    def test_all_slugs_are_unique(self) -> None:
        slugs = [opt.slug for opt in ROOM_CATALOG]
        assert len(set(slugs)) == len(slugs)

    def test_all_tiers_are_positive(self) -> None:
        for opt in ROOM_CATALOG:
            assert opt.tier >= 1

    def test_all_names_are_two_words(self) -> None:
        """Enforce the two-word naming convention from docs/aesthetic.md."""
        for opt in ROOM_CATALOG:
            words = opt.name.split()
            assert len(words) == 2, (
                f"Room item '{opt.slug}' has name '{opt.name}'"
                " -- expected exactly two words"
            )

    def test_all_slugs_are_hyphenated_lowercase(self) -> None:
        for opt in ROOM_CATALOG:
            assert opt.slug == opt.slug.lower(), f"Slug '{opt.slug}' is not lowercase"
            assert " " not in opt.slug, f"Slug '{opt.slug}' contains a space"

    def test_all_descriptions_non_empty(self) -> None:
        for opt in ROOM_CATALOG:
            assert len(opt.description) > 0

    def test_catalog_ordered_by_tier(self) -> None:
        """Tiers must be non-decreasing across the catalog."""
        tiers = [opt.tier for opt in ROOM_CATALOG]
        assert tiers == sorted(tiers)


# ---------------------------------------------------------------------------
# Tier coverage
# ---------------------------------------------------------------------------


class TestTierCoverage:
    def test_tier_1_entries_exist(self) -> None:
        assert any(opt.tier == _TIER_1_MIN_LEVEL for opt in ROOM_CATALOG)

    def test_tier_2_entries_exist(self) -> None:
        assert any(opt.tier == _TIER_2_MIN_LEVEL for opt in ROOM_CATALOG)

    def test_tier_3_entries_exist(self) -> None:
        assert any(opt.tier == _TIER_3_MIN_LEVEL for opt in ROOM_CATALOG)

    def test_tier_4_entries_exist(self) -> None:
        assert any(opt.tier == _TIER_4_MIN_LEVEL for opt in ROOM_CATALOG)

    def test_tier_boundaries_are_ordered(self) -> None:
        assert _TIER_1_MIN_LEVEL < _TIER_2_MIN_LEVEL
        assert _TIER_2_MIN_LEVEL < _TIER_3_MIN_LEVEL
        assert _TIER_3_MIN_LEVEL < _TIER_4_MIN_LEVEL


# ---------------------------------------------------------------------------
# rooms_for_level
# ---------------------------------------------------------------------------


class TestRoomsForLevel:
    def test_level_zero_returns_empty(self) -> None:
        assert rooms_for_level(0) == ()

    def test_negative_level_returns_empty(self) -> None:
        assert rooms_for_level(-1) == ()

    def test_level_one_returns_tier_1_only(self) -> None:
        result = rooms_for_level(1)
        assert len(result) > 0
        for opt in result:
            assert opt.tier == _TIER_1_MIN_LEVEL

    def test_level_three_returns_tier_1_only(self) -> None:
        result = rooms_for_level(3)
        for opt in result:
            assert opt.tier < _TIER_2_MIN_LEVEL

    def test_level_four_includes_tier_2(self) -> None:
        result = rooms_for_level(4)
        tier2_slugs = {opt.slug for opt in result if opt.tier == _TIER_2_MIN_LEVEL}
        assert len(tier2_slugs) > 0

    def test_level_six_excludes_tier_3(self) -> None:
        result = rooms_for_level(6)
        for opt in result:
            assert opt.tier < _TIER_3_MIN_LEVEL

    def test_level_seven_includes_tier_3(self) -> None:
        result = rooms_for_level(7)
        tier3_slugs = {opt.slug for opt in result if opt.tier == _TIER_3_MIN_LEVEL}
        assert len(tier3_slugs) > 0

    def test_level_ten_excludes_tier_4(self) -> None:
        result = rooms_for_level(10)
        for opt in result:
            assert opt.tier < _TIER_4_MIN_LEVEL

    def test_level_eleven_includes_tier_4(self) -> None:
        result = rooms_for_level(11)
        tier4_slugs = {opt.slug for opt in result if opt.tier == _TIER_4_MIN_LEVEL}
        assert len(tier4_slugs) > 0

    def test_very_high_level_returns_all(self) -> None:
        result = rooms_for_level(100)
        assert {opt.slug for opt in result} == {opt.slug for opt in ROOM_CATALOG}

    def test_returns_tuple(self) -> None:
        assert isinstance(rooms_for_level(0), tuple)
        assert isinstance(rooms_for_level(5), tuple)

    def test_result_is_subset_of_catalog(self) -> None:
        catalog_slugs = {opt.slug for opt in ROOM_CATALOG}
        for level in (1, 4, 7, 11):
            for opt in rooms_for_level(level):
                assert opt.slug in catalog_slugs

    def test_result_count_increases_with_level(self) -> None:
        counts = [len(rooms_for_level(lvl)) for lvl in range(0, 15)]
        for i in range(len(counts) - 1):
            assert counts[i] <= counts[i + 1]

    def test_exactly_tier1_count_at_level_one(self) -> None:
        tier1_count = sum(1 for opt in ROOM_CATALOG if opt.tier == _TIER_1_MIN_LEVEL)
        assert len(rooms_for_level(1)) == tier1_count

    def test_tier1_and_tier2_count_at_level_four(self) -> None:
        expected = sum(
            1
            for opt in ROOM_CATALOG
            if opt.tier in (_TIER_1_MIN_LEVEL, _TIER_2_MIN_LEVEL)
        )
        assert len(rooms_for_level(4)) == expected


# ---------------------------------------------------------------------------
# Integration: catalog plugs into levels module
# ---------------------------------------------------------------------------


class TestCatalogIntegrationWithLevels:
    def test_room_options_for_level_accepts_catalog(self) -> None:
        """Verify ROOM_CATALOG is accepted by levels.room_options_for_level."""
        from uuid import uuid4

        from sender_frenz.common.levels import room_options_for_level
        from sender_frenz.common.models import Room
        from sender_frenz.common.types import AvatarId, RoomId

        room = Room(
            id=RoomId(uuid4()),
            avatar_id=AvatarId(uuid4()),
            level=1,
            applied_upgrades=(),
        )
        result = room_options_for_level(room, ROOM_CATALOG)
        assert isinstance(result, tuple)
        assert len(result) > 0

    def test_already_applied_upgrade_excluded(self) -> None:
        from uuid import uuid4

        from sender_frenz.common.levels import room_options_for_level
        from sender_frenz.common.models import Room
        from sender_frenz.common.types import AvatarId, RoomId

        tier1_slug = next(
            opt.slug for opt in ROOM_CATALOG if opt.tier == _TIER_1_MIN_LEVEL
        )
        room = Room(
            id=RoomId(uuid4()),
            avatar_id=AvatarId(uuid4()),
            level=1,
            applied_upgrades=(tier1_slug,),
        )
        result = room_options_for_level(room, ROOM_CATALOG)
        assert tier1_slug not in {opt.slug for opt in result}

    def test_apply_level_up_end_to_end(self) -> None:
        """apply_level_up works with both SKIN_CATALOG and ROOM_CATALOG together."""
        from uuid import uuid4

        from sender_frenz.character_builder.catalog import SKIN_CATALOG
        from sender_frenz.common.levels import apply_level_up
        from sender_frenz.common.models import (
            Avatar,
            Level,
            NeedState,
            Room,
            SocialState,
            VampiricStage,
        )
        from sender_frenz.common.types import AvatarId, RoomId

        avatar = Avatar(
            id=AvatarId(uuid4()),
            needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
            social=SocialState(
                score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
            ),
            level=Level(current=1, skin_upgrades=(), room_upgrades=()),
            created_at=0.0,
        )
        room = Room(
            id=RoomId(uuid4()),
            avatar_id=avatar.id,
            level=1,
            applied_upgrades=(),
        )

        # Pick the first available skin and room upgrade at level 1.
        from sender_frenz.common.levels import (
            room_options_for_level,
            skin_options_for_level,
        )

        skin_slug = skin_options_for_level(avatar, SKIN_CATALOG)[0].slug
        room_slug = room_options_for_level(room, ROOM_CATALOG)[0].slug

        new_avatar, new_room = apply_level_up(
            avatar, room, skin_slug, room_slug, SKIN_CATALOG, ROOM_CATALOG
        )

        assert new_avatar.level.current == 2
        assert skin_slug in new_avatar.level.skin_upgrades
        assert new_room.level == 2
        assert room_slug in new_room.applied_upgrades

    def test_slug_uniqueness_enforced_by_upgrade_option(self) -> None:
        with pytest.raises(ValueError, match="slug"):
            UpgradeOption(slug="", name="Bad Entry", tier=1, description="test")
