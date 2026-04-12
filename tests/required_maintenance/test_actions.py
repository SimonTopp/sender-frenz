"""Tests for sender_frenz.required_maintenance.actions."""

import random
from uuid import uuid4

import pytest

from sender_frenz.common.config import PRODUCTION_PACE, TEST_PACE
from sender_frenz.common.decay import DecayConfig
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.quips import QuipTrigger, default_quip_caller
from sender_frenz.common.types import AvatarId
from sender_frenz.required_maintenance.actions import (
    CLEAN_RESTORE,
    FEED_RESTORE,
    HUNGER_IDEAL_MAX,
    HYGIENE_IDEAL_MAX,
    ActionResult,
    clean,
    feed,
    over_nourished_decay,
    over_scrubbed_decay,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FIXED_QUIP_CALLER = default_quip_caller(rng=random.Random(0))
_NOW = 1000.0  # arbitrary timestamp


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
# Constants
# ---------------------------------------------------------------------------


class TestActionConstants:
    def test_feed_restore_value(self) -> None:
        assert pytest.approx(0.40) == FEED_RESTORE

    def test_clean_restore_value(self) -> None:
        assert pytest.approx(0.50) == CLEAN_RESTORE

    def test_hunger_ideal_max_value(self) -> None:
        assert pytest.approx(0.80) == HUNGER_IDEAL_MAX

    def test_hygiene_ideal_max_value(self) -> None:
        assert pytest.approx(0.90) == HYGIENE_IDEAL_MAX


# ---------------------------------------------------------------------------
# over_nourished_decay
# ---------------------------------------------------------------------------


class TestOverNourishedDecay:
    def test_meter_is_hunger(self) -> None:
        decay = over_nourished_decay(PRODUCTION_PACE)
        assert decay.meter == "hunger"

    def test_rate_scales_with_pace(self) -> None:
        prod = over_nourished_decay(PRODUCTION_PACE)
        test = over_nourished_decay(TEST_PACE)
        assert test.rate_per_hour == pytest.approx(prod.rate_per_hour * 720.0)

    def test_condition_false_below_ideal_max(self) -> None:
        decay = over_nourished_decay(PRODUCTION_PACE)
        av = _avatar(hunger=HUNGER_IDEAL_MAX - 0.01)
        assert decay.condition(av) is False

    def test_condition_false_at_ideal_max(self) -> None:
        decay = over_nourished_decay(PRODUCTION_PACE)
        av = _avatar(hunger=HUNGER_IDEAL_MAX)
        assert decay.condition(av) is False

    def test_condition_true_above_ideal_max(self) -> None:
        decay = over_nourished_decay(PRODUCTION_PACE)
        av = _avatar(hunger=HUNGER_IDEAL_MAX + 0.01)
        assert decay.condition(av) is True

    def test_doubles_hunger_drain_rate(self) -> None:
        extra = over_nourished_decay(PRODUCTION_PACE)
        cfg = DecayConfig.from_pace(PRODUCTION_PACE, extra_decays=(extra,))
        av = _avatar(hunger=HUNGER_IDEAL_MAX + 0.01)
        base_cfg = DecayConfig.from_pace(PRODUCTION_PACE)
        assert cfg.effective_rate(av, "hunger") == pytest.approx(
            base_cfg.effective_rate(av, "hunger") * 2.0
        )


# ---------------------------------------------------------------------------
# over_scrubbed_decay
# ---------------------------------------------------------------------------


class TestOverScrubbedDecay:
    def test_meter_is_hygiene(self) -> None:
        decay = over_scrubbed_decay(PRODUCTION_PACE)
        assert decay.meter == "hygiene"

    def test_rate_scales_with_pace(self) -> None:
        prod = over_scrubbed_decay(PRODUCTION_PACE)
        test = over_scrubbed_decay(TEST_PACE)
        assert test.rate_per_hour == pytest.approx(prod.rate_per_hour * 720.0)

    def test_condition_false_below_ideal_max(self) -> None:
        decay = over_scrubbed_decay(PRODUCTION_PACE)
        av = _avatar(hygiene=HYGIENE_IDEAL_MAX - 0.01)
        assert decay.condition(av) is False

    def test_condition_false_at_ideal_max(self) -> None:
        decay = over_scrubbed_decay(PRODUCTION_PACE)
        av = _avatar(hygiene=HYGIENE_IDEAL_MAX)
        assert decay.condition(av) is False

    def test_condition_true_above_ideal_max(self) -> None:
        decay = over_scrubbed_decay(PRODUCTION_PACE)
        av = _avatar(hygiene=HYGIENE_IDEAL_MAX + 0.01)
        assert decay.condition(av) is True


# ---------------------------------------------------------------------------
# feed
# ---------------------------------------------------------------------------


class TestFeed:
    def test_increases_hunger(self) -> None:
        av = _avatar(hunger=0.3)
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.hunger == pytest.approx(0.3 + FEED_RESTORE)

    def test_clamps_hunger_at_one(self) -> None:
        av = _avatar(hunger=0.9)
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.hunger == pytest.approx(1.0)

    def test_returns_action_result(self) -> None:
        av = _avatar()
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert isinstance(result, ActionResult)

    def test_quip_is_string(self) -> None:
        av = _avatar()
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert isinstance(result.quip, str)
        assert len(result.quip) > 0

    def test_feed_trigger_when_below_ideal_max(self) -> None:
        # hunger=0.1 + 0.4 = 0.5 < 0.8 → FEED trigger
        triggered: list[QuipTrigger] = []

        def recording_caller(t: QuipTrigger) -> str:
            triggered.append(t)
            return "quip"

        av = _avatar(hunger=0.1)
        feed(av, _NOW, recording_caller)
        assert triggered == [QuipTrigger.FEED]

    def test_over_nourished_trigger_when_above_ideal_max(self) -> None:
        # hunger=0.6 + 0.4 = 1.0 > 0.8 → OVER_NOURISHED trigger
        triggered: list[QuipTrigger] = []

        def recording_caller(t: QuipTrigger) -> str:
            triggered.append(t)
            return "quip"

        av = _avatar(hunger=0.6)
        feed(av, _NOW, recording_caller)
        assert triggered == [QuipTrigger.OVER_NOURISHED]

    def test_updates_last_updated_to_now(self) -> None:
        av = _avatar()
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.last_updated == pytest.approx(_NOW)

    def test_does_not_change_hygiene(self) -> None:
        av = _avatar(hygiene=0.7)
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.hygiene == pytest.approx(0.7)

    def test_does_not_change_social(self) -> None:
        av = _avatar()
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social == av.social

    def test_preserves_id_level_created_at(self) -> None:
        av = _avatar()
        result = feed(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.id == av.id
        assert result.avatar.level == av.level
        assert result.avatar.created_at == av.created_at


# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------


class TestClean:
    def test_increases_hygiene(self) -> None:
        av = _avatar(hygiene=0.3)
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.hygiene == pytest.approx(0.3 + CLEAN_RESTORE)

    def test_clamps_hygiene_at_one(self) -> None:
        av = _avatar(hygiene=0.8)
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.hygiene == pytest.approx(1.0)

    def test_returns_action_result(self) -> None:
        av = _avatar()
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert isinstance(result, ActionResult)

    def test_quip_is_string(self) -> None:
        av = _avatar()
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert isinstance(result.quip, str)
        assert len(result.quip) > 0

    def test_clean_trigger_when_below_ideal_max(self) -> None:
        # hygiene=0.2 + 0.5 = 0.7 < 0.9 → CLEAN trigger
        triggered: list[QuipTrigger] = []

        def recording_caller(t: QuipTrigger) -> str:
            triggered.append(t)
            return "quip"

        av = _avatar(hygiene=0.2)
        clean(av, _NOW, recording_caller)
        assert triggered == [QuipTrigger.CLEAN]

    def test_over_scrubbed_trigger_when_above_ideal_max(self) -> None:
        # hygiene=0.6 + 0.5 = 1.0 > 0.9 → OVER_SCRUBBED trigger
        triggered: list[QuipTrigger] = []

        def recording_caller(t: QuipTrigger) -> str:
            triggered.append(t)
            return "quip"

        av = _avatar(hygiene=0.6)
        clean(av, _NOW, recording_caller)
        assert triggered == [QuipTrigger.OVER_SCRUBBED]

    def test_updates_last_updated_to_now(self) -> None:
        av = _avatar()
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.last_updated == pytest.approx(_NOW)

    def test_does_not_change_hunger(self) -> None:
        av = _avatar(hunger=0.6)
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs.hunger == pytest.approx(0.6)

    def test_does_not_change_social(self) -> None:
        av = _avatar()
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social == av.social

    def test_preserves_id_level_created_at(self) -> None:
        av = _avatar()
        result = clean(av, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.id == av.id
        assert result.avatar.level == av.level
        assert result.avatar.created_at == av.created_at
