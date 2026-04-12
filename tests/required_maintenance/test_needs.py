"""Tests for sender_frenz.required_maintenance.needs."""

from uuid import uuid4

import pytest

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId
from sender_frenz.required_maintenance.actions import (
    HUNGER_IDEAL_MAX,
    HYGIENE_IDEAL_MAX,
)
from sender_frenz.required_maintenance.needs import (
    NeedsSummary,
    is_dirty,
    is_hungry,
    is_over_nourished,
    is_over_scrubbed,
    needs_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _avatar(hunger: float = 0.5, hygiene: float = 0.5) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=0.0),
        social=SocialState(
            score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
        ),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# is_hungry
# ---------------------------------------------------------------------------


class TestIsHungry:
    def test_hungry_at_zero(self) -> None:
        assert is_hungry(_avatar(hunger=0.0)) is True

    def test_hungry_at_threshold(self) -> None:
        assert is_hungry(_avatar(hunger=0.2)) is True

    def test_not_hungry_above_threshold(self) -> None:
        assert is_hungry(_avatar(hunger=0.21)) is False

    def test_not_hungry_when_full(self) -> None:
        assert is_hungry(_avatar(hunger=1.0)) is False

    def test_custom_threshold_lower(self) -> None:
        assert is_hungry(_avatar(hunger=0.15), threshold=0.1) is False

    def test_custom_threshold_higher(self) -> None:
        assert is_hungry(_avatar(hunger=0.3), threshold=0.5) is True


# ---------------------------------------------------------------------------
# is_dirty
# ---------------------------------------------------------------------------


class TestIsDirty:
    def test_dirty_at_zero(self) -> None:
        assert is_dirty(_avatar(hygiene=0.0)) is True

    def test_dirty_at_threshold(self) -> None:
        assert is_dirty(_avatar(hygiene=0.2)) is True

    def test_not_dirty_above_threshold(self) -> None:
        assert is_dirty(_avatar(hygiene=0.21)) is False

    def test_not_dirty_when_clean(self) -> None:
        assert is_dirty(_avatar(hygiene=1.0)) is False

    def test_custom_threshold(self) -> None:
        assert is_dirty(_avatar(hygiene=0.4), threshold=0.5) is True


# ---------------------------------------------------------------------------
# is_over_nourished
# ---------------------------------------------------------------------------


class TestIsOverNourished:
    def test_true_when_above_ideal_max(self) -> None:
        assert is_over_nourished(_avatar(hunger=HUNGER_IDEAL_MAX + 0.01)) is True

    def test_false_at_ideal_max(self) -> None:
        assert is_over_nourished(_avatar(hunger=HUNGER_IDEAL_MAX)) is False

    def test_false_below_ideal_max(self) -> None:
        assert is_over_nourished(_avatar(hunger=HUNGER_IDEAL_MAX - 0.01)) is False

    def test_false_at_zero(self) -> None:
        assert is_over_nourished(_avatar(hunger=0.0)) is False


# ---------------------------------------------------------------------------
# is_over_scrubbed
# ---------------------------------------------------------------------------


class TestIsOverScrubbed:
    def test_true_when_above_ideal_max(self) -> None:
        assert is_over_scrubbed(_avatar(hygiene=HYGIENE_IDEAL_MAX + 0.01)) is True

    def test_false_at_ideal_max(self) -> None:
        assert is_over_scrubbed(_avatar(hygiene=HYGIENE_IDEAL_MAX)) is False

    def test_false_below_ideal_max(self) -> None:
        assert is_over_scrubbed(_avatar(hygiene=HYGIENE_IDEAL_MAX - 0.01)) is False

    def test_false_at_zero(self) -> None:
        assert is_over_scrubbed(_avatar(hygiene=0.0)) is False


# ---------------------------------------------------------------------------
# NeedsSummary / needs_summary
# ---------------------------------------------------------------------------


class TestNeedsSummary:
    def test_hunger_and_hygiene_fields_match_avatar(self) -> None:
        av = _avatar(hunger=0.6, hygiene=0.7)
        summary = needs_summary(av)
        assert summary.hunger == pytest.approx(0.6)
        assert summary.hygiene == pytest.approx(0.7)

    def test_hungry_flag_set_when_starving(self) -> None:
        av = _avatar(hunger=0.1)
        summary = needs_summary(av)
        assert summary.hungry is True

    def test_hungry_flag_clear_when_fed(self) -> None:
        av = _avatar(hunger=0.9)
        summary = needs_summary(av)
        assert summary.hungry is False

    def test_dirty_flag_set_when_filthy(self) -> None:
        av = _avatar(hygiene=0.1)
        summary = needs_summary(av)
        assert summary.dirty is True

    def test_dirty_flag_clear_when_clean(self) -> None:
        av = _avatar(hygiene=0.9)
        summary = needs_summary(av)
        assert summary.dirty is False

    def test_over_nourished_flag_set(self) -> None:
        av = _avatar(hunger=HUNGER_IDEAL_MAX + 0.05)
        summary = needs_summary(av)
        assert summary.over_nourished is True

    def test_over_nourished_flag_clear(self) -> None:
        av = _avatar(hunger=HUNGER_IDEAL_MAX - 0.05)
        summary = needs_summary(av)
        assert summary.over_nourished is False

    def test_over_scrubbed_flag_set(self) -> None:
        av = _avatar(hygiene=HYGIENE_IDEAL_MAX + 0.05)
        summary = needs_summary(av)
        assert summary.over_scrubbed is True

    def test_over_scrubbed_flag_clear(self) -> None:
        av = _avatar(hygiene=HYGIENE_IDEAL_MAX - 0.05)
        summary = needs_summary(av)
        assert summary.over_scrubbed is False

    def test_returns_needs_summary_instance(self) -> None:
        av = _avatar()
        assert isinstance(needs_summary(av), NeedsSummary)
