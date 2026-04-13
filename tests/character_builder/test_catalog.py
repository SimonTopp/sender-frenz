"""Tests for sender_frenz.character_builder.catalog."""

import pytest

from sender_frenz.character_builder.catalog import (
    _TIER_1_MIN_LEVEL,
    _TIER_2_MIN_LEVEL,
    _TIER_3_MIN_LEVEL,
    _TIER_4_MIN_LEVEL,
    SKIN_CATALOG,
    skins_for_level,
)
from sender_frenz.common.levels import (
    UpgradeOption,
)

# ---------------------------------------------------------------------------
# SKIN_CATALOG structure
# ---------------------------------------------------------------------------


class TestSkinCatalogStructure:
    def test_catalog_is_not_empty(self) -> None:
        assert len(SKIN_CATALOG) > 0

    def test_all_entries_are_upgrade_options(self) -> None:
        for entry in SKIN_CATALOG:
            assert isinstance(entry, UpgradeOption)

    def test_all_slugs_are_unique(self) -> None:
        slugs = [opt.slug for opt in SKIN_CATALOG]
        assert len(set(slugs)) == len(slugs)

    def test_all_tiers_are_positive(self) -> None:
        for opt in SKIN_CATALOG:
            assert opt.tier >= 1

    def test_all_names_are_two_words(self) -> None:
        """Enforce the two-word naming convention from docs/aesthetic.md."""
        for opt in SKIN_CATALOG:
            words = opt.name.split()
            assert len(words) == 2, (
                f"Skin '{opt.slug}' has name '{opt.name}' — expected exactly two words"
            )

    def test_all_slugs_are_hyphenated_lowercase(self) -> None:
        """Slugs must be lowercase with hyphens, no spaces or uppercase."""
        for opt in SKIN_CATALOG:
            assert opt.slug == opt.slug.lower(), f"Slug '{opt.slug}' is not lowercase"
            assert " " not in opt.slug, f"Slug '{opt.slug}' contains a space"

    def test_all_descriptions_non_empty(self) -> None:
        for opt in SKIN_CATALOG:
            assert len(opt.description) > 0

    def test_catalog_ordered_by_tier(self) -> None:
        """Tiers must be non-decreasing across the catalog."""
        tiers = [opt.tier for opt in SKIN_CATALOG]
        assert tiers == sorted(tiers)


# ---------------------------------------------------------------------------
# Tier coverage — catalog contains entries at each defined tier
# ---------------------------------------------------------------------------


class TestTierCoverage:
    def test_tier_1_entries_exist(self) -> None:
        tier1 = [opt for opt in SKIN_CATALOG if opt.tier == _TIER_1_MIN_LEVEL]
        assert len(tier1) >= 1

    def test_tier_2_entries_exist(self) -> None:
        tier2 = [opt for opt in SKIN_CATALOG if opt.tier == _TIER_2_MIN_LEVEL]
        assert len(tier2) >= 1

    def test_tier_3_entries_exist(self) -> None:
        tier3 = [opt for opt in SKIN_CATALOG if opt.tier == _TIER_3_MIN_LEVEL]
        assert len(tier3) >= 1

    def test_tier_4_entries_exist(self) -> None:
        tier4 = [opt for opt in SKIN_CATALOG if opt.tier == _TIER_4_MIN_LEVEL]
        assert len(tier4) >= 1

    def test_tier_boundaries_are_ordered(self) -> None:
        assert _TIER_1_MIN_LEVEL < _TIER_2_MIN_LEVEL
        assert _TIER_2_MIN_LEVEL < _TIER_3_MIN_LEVEL
        assert _TIER_3_MIN_LEVEL < _TIER_4_MIN_LEVEL


# ---------------------------------------------------------------------------
# skins_for_level
# ---------------------------------------------------------------------------


class TestSkinsForLevel:
    def test_level_zero_returns_empty(self) -> None:
        assert skins_for_level(0) == ()

    def test_negative_level_returns_empty(self) -> None:
        assert skins_for_level(-5) == ()

    def test_level_one_returns_tier_1_only(self) -> None:
        result = skins_for_level(1)
        assert len(result) > 0
        for opt in result:
            assert opt.tier == _TIER_1_MIN_LEVEL

    def test_level_three_returns_tier_1_only(self) -> None:
        """Tier-2 requires level 4; level 3 must not include tier-2 entries."""
        result = skins_for_level(3)
        for opt in result:
            assert opt.tier < _TIER_2_MIN_LEVEL

    def test_level_four_includes_tier_2(self) -> None:
        result = skins_for_level(4)
        tier2_slugs = {opt.slug for opt in result if opt.tier == _TIER_2_MIN_LEVEL}
        assert len(tier2_slugs) > 0

    def test_level_six_excludes_tier_3(self) -> None:
        """Tier-3 requires level 7; level 6 must not include tier-3 entries."""
        result = skins_for_level(6)
        for opt in result:
            assert opt.tier < _TIER_3_MIN_LEVEL

    def test_level_seven_includes_tier_3(self) -> None:
        result = skins_for_level(7)
        tier3_slugs = {opt.slug for opt in result if opt.tier == _TIER_3_MIN_LEVEL}
        assert len(tier3_slugs) > 0

    def test_level_ten_excludes_tier_4(self) -> None:
        """Tier-4 requires level 11; level 10 must not include tier-4 entries."""
        result = skins_for_level(10)
        for opt in result:
            assert opt.tier < _TIER_4_MIN_LEVEL

    def test_level_eleven_includes_tier_4(self) -> None:
        result = skins_for_level(11)
        tier4_slugs = {opt.slug for opt in result if opt.tier == _TIER_4_MIN_LEVEL}
        assert len(tier4_slugs) > 0

    def test_very_high_level_returns_all(self) -> None:
        result = skins_for_level(100)
        assert {opt.slug for opt in result} == {opt.slug for opt in SKIN_CATALOG}

    def test_returns_tuple(self) -> None:
        assert isinstance(skins_for_level(0), tuple)
        assert isinstance(skins_for_level(5), tuple)

    def test_result_is_subset_of_catalog(self) -> None:
        catalog_slugs = {opt.slug for opt in SKIN_CATALOG}
        for level in (1, 4, 7, 11):
            for opt in skins_for_level(level):
                assert opt.slug in catalog_slugs

    def test_result_count_increases_with_level(self) -> None:
        """More levels should unlock more skins, never fewer."""
        counts = [len(skins_for_level(lvl)) for lvl in range(0, 15)]
        for i in range(len(counts) - 1):
            assert counts[i] <= counts[i + 1]

    def test_exactly_tier1_count_at_level_one(self) -> None:
        tier1_count = sum(1 for opt in SKIN_CATALOG if opt.tier == _TIER_1_MIN_LEVEL)
        assert len(skins_for_level(1)) == tier1_count

    def test_tier1_and_tier2_count_at_level_four(self) -> None:
        expected = sum(
            1
            for opt in SKIN_CATALOG
            if opt.tier in (_TIER_1_MIN_LEVEL, _TIER_2_MIN_LEVEL)
        )
        assert len(skins_for_level(4)) == expected


# ---------------------------------------------------------------------------
# Integration: catalog entries plug into levels.skin_options_for_level
# ---------------------------------------------------------------------------


class TestCatalogIntegrationWithLevels:
    def test_skin_options_for_level_accepts_catalog(self) -> None:
        """Verify SKIN_CATALOG is accepted by the levels module without error."""
        from uuid import uuid4

        from sender_frenz.common.levels import skin_options_for_level
        from sender_frenz.common.models import (
            Avatar,
            Level,
            NeedState,
            SocialState,
            VampiricStage,
        )
        from sender_frenz.common.types import AvatarId

        avatar = Avatar(
            id=AvatarId(uuid4()),
            needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
            social=SocialState(
                score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
            ),
            level=Level(current=1, skin_upgrades=(), room_upgrades=()),
            created_at=0.0,
        )
        result = skin_options_for_level(avatar, SKIN_CATALOG)
        assert isinstance(result, tuple)
        assert len(result) > 0

    def test_already_applied_skin_excluded(self) -> None:
        """Applied slugs should be excluded by skin_options_for_level."""
        from uuid import uuid4

        from sender_frenz.character_builder.catalog import SKIN_CATALOG
        from sender_frenz.common.levels import skin_options_for_level
        from sender_frenz.common.models import (
            Avatar,
            Level,
            NeedState,
            SocialState,
            VampiricStage,
        )
        from sender_frenz.common.types import AvatarId

        tier1_slug = next(
            opt.slug for opt in SKIN_CATALOG if opt.tier == _TIER_1_MIN_LEVEL
        )
        avatar = Avatar(
            id=AvatarId(uuid4()),
            needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
            social=SocialState(
                score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
            ),
            level=Level(current=1, skin_upgrades=(tier1_slug,), room_upgrades=()),
            created_at=0.0,
        )
        result = skin_options_for_level(avatar, SKIN_CATALOG)
        result_slugs = {opt.slug for opt in result}
        assert tier1_slug not in result_slugs

    def test_slug_uniqueness_enforced_by_upgrade_option(self) -> None:
        """UpgradeOption construction raises on empty slug (sanity check)."""
        with pytest.raises(ValueError, match="slug"):
            UpgradeOption(slug="", name="Bad Entry", tier=1, description="test")
