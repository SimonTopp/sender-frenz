"""Tests for sender_frenz.common.decay."""

from uuid import uuid4

import pytest

from sender_frenz.common.config import PRODUCTION_PACE, TEST_PACE, GamePace
from sender_frenz.common.decay import (
    DecayConfig,
    apply_decay,
    apply_need_decay,
    apply_social_decay,
    time_until_critical,
)
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROD_CONFIG = DecayConfig.from_pace(PRODUCTION_PACE)
_TEST_CONFIG = DecayConfig.from_pace(TEST_PACE)
_ONE_HOUR = 3600.0


def _needs(hunger: float = 1.0, hygiene: float = 1.0) -> NeedState:
    return NeedState(hunger=hunger, hygiene=hygiene, last_updated=0.0)


def _social(
    score: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
    last_interaction: float = 0.0,
) -> SocialState:
    return SocialState(
        score=score,
        vampiric_stage=stage,
        last_interaction=last_interaction,
    )


def _avatar(hunger: float = 1.0, hygiene: float = 1.0, score: float = 1.0) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=_needs(hunger, hygiene),
        social=_social(score),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# DecayConfig.from_pace
# ---------------------------------------------------------------------------


class TestDecayConfigFromPace:
    def test_production_rates_match_documented_values(self) -> None:
        cfg = DecayConfig.from_pace(PRODUCTION_PACE)
        assert cfg.hunger_rate == pytest.approx(1.0 / 8.0)
        assert cfg.hygiene_rate == pytest.approx(1.0 / 12.0)
        assert cfg.social_rate == pytest.approx(1.0 / 24.0)
        assert cfg.vampiric_advance_hours == pytest.approx(12.0)
        assert cfg.vampiric_retreat_rate == pytest.approx(0.5)

    def test_test_pace_rates_are_720x_production(self) -> None:
        prod = DecayConfig.from_pace(PRODUCTION_PACE)
        test = DecayConfig.from_pace(TEST_PACE)
        assert test.hunger_rate == pytest.approx(prod.hunger_rate * 720.0)
        assert test.hygiene_rate == pytest.approx(prod.hygiene_rate * 720.0)
        assert test.social_rate == pytest.approx(prod.social_rate * 720.0)
        assert test.vampiric_advance_hours == pytest.approx(
            prod.vampiric_advance_hours / 720.0
        )
        assert test.vampiric_retreat_rate == pytest.approx(
            prod.vampiric_retreat_rate * 720.0
        )

    def test_custom_pace_scales_correctly(self) -> None:
        cfg = DecayConfig.from_pace(GamePace(time_scale=2.0))
        assert cfg.hunger_rate == pytest.approx((1.0 / 8.0) * 2.0)


# ---------------------------------------------------------------------------
# apply_need_decay
# ---------------------------------------------------------------------------


class TestApplyNeedDecay:
    def test_zero_elapsed_returns_same_values(self) -> None:
        needs = _needs(hunger=0.8, hygiene=0.6)
        result = apply_need_decay(needs, 0.0, _PROD_CONFIG)
        assert result.hunger == pytest.approx(0.8)
        assert result.hygiene == pytest.approx(0.6)

    def test_hunger_decreases_over_time(self) -> None:
        needs = _needs(hunger=1.0)
        result = apply_need_decay(needs, _ONE_HOUR, _PROD_CONFIG)
        assert result.hunger < 1.0

    def test_hygiene_decreases_over_time(self) -> None:
        needs = _needs(hygiene=1.0)
        result = apply_need_decay(needs, _ONE_HOUR, _PROD_CONFIG)
        assert result.hygiene < 1.0

    def test_hunger_empties_in_8_hours(self) -> None:
        needs = _needs(hunger=1.0)
        result = apply_need_decay(needs, 8 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hunger == pytest.approx(0.0, abs=1e-9)

    def test_hygiene_empties_in_12_hours(self) -> None:
        needs = _needs(hygiene=1.0)
        result = apply_need_decay(needs, 12 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hygiene == pytest.approx(0.0, abs=1e-9)

    def test_hunger_clamps_at_zero(self) -> None:
        needs = _needs(hunger=0.1)
        result = apply_need_decay(needs, 100 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hunger == 0.0

    def test_hygiene_clamps_at_zero(self) -> None:
        needs = _needs(hygiene=0.1)
        result = apply_need_decay(needs, 100 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hygiene == 0.0

    def test_last_updated_advances(self) -> None:
        needs = _needs()
        result = apply_need_decay(needs, 500.0, _PROD_CONFIG)
        assert result.last_updated == pytest.approx(500.0)

    def test_returns_new_instance(self) -> None:
        needs = _needs()
        result = apply_need_decay(needs, _ONE_HOUR, _PROD_CONFIG)
        assert result is not needs


# ---------------------------------------------------------------------------
# apply_social_decay
# ---------------------------------------------------------------------------


class TestApplySocialDecay:
    def test_zero_elapsed_returns_same_values(self) -> None:
        social = _social(score=0.8)
        result = apply_social_decay(social, 0.0, _PROD_CONFIG)
        assert result.score == pytest.approx(0.8)
        assert result.vampiric_stage == VampiricStage.NONE

    def test_score_decreases_over_time(self) -> None:
        social = _social(score=1.0)
        result = apply_social_decay(social, _ONE_HOUR, _PROD_CONFIG)
        assert result.score < 1.0

    def test_social_empties_in_24_hours(self) -> None:
        social = _social(score=1.0)
        result = apply_social_decay(social, 24 * _ONE_HOUR, _PROD_CONFIG)
        assert result.score == pytest.approx(0.0, abs=1e-9)

    def test_score_clamps_at_zero(self) -> None:
        social = _social(score=0.1)
        result = apply_social_decay(social, 100 * _ONE_HOUR, _PROD_CONFIG)
        assert result.score == 0.0

    def test_vampiric_stage_advances_when_score_zero(self) -> None:
        # score=0, elapsed = 2 * vampiric_advance_hours → 2 stage advances
        advance_secs = _PROD_CONFIG.vampiric_advance_hours * _ONE_HOUR * 2
        social = _social(score=0.0, stage=VampiricStage.NONE)
        result = apply_social_decay(social, advance_secs, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.GAUNT

    def test_vampiric_stage_clamps_at_vampiric(self) -> None:
        social = _social(score=0.0, stage=VampiricStage.HOLLOW)
        result = apply_social_decay(social, 1000 * _ONE_HOUR, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.VAMPIRIC

    def test_vampiric_stage_retreats_when_score_positive(self) -> None:
        # retreat_rate=0.5 stages/hour; 2 hours → 1 stage retreat
        retreat_secs = 2 * _ONE_HOUR
        social = _social(score=0.5, stage=VampiricStage.GAUNT)
        result = apply_social_decay(social, retreat_secs, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.PALLOR

    def test_no_retreat_below_none(self) -> None:
        # score=0.5 decays at 1/24 Meter/hour; after 1h score ≈ 0.458 (still > 0)
        # retreat logic fires but stage is already NONE — must clamp at NONE.
        social = _social(score=0.5, stage=VampiricStage.NONE)
        result = apply_social_decay(social, _ONE_HOUR, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.NONE

    def test_last_interaction_advances(self) -> None:
        social = _social()
        result = apply_social_decay(social, 300.0, _PROD_CONFIG)
        assert result.last_interaction == pytest.approx(300.0)

    def test_returns_new_instance(self) -> None:
        social = _social()
        result = apply_social_decay(social, _ONE_HOUR, _PROD_CONFIG)
        assert result is not social


# ---------------------------------------------------------------------------
# apply_decay
# ---------------------------------------------------------------------------


class TestApplyDecay:
    def test_applies_both_need_and_social_decay(self) -> None:
        av = _avatar(hunger=1.0, hygiene=1.0, score=1.0)
        result = apply_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result.needs.hunger < 1.0
        assert result.needs.hygiene < 1.0
        assert result.social.score < 1.0

    def test_preserves_id_level_created_at(self) -> None:
        av = _avatar()
        result = apply_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result.id == av.id
        assert result.level == av.level
        assert result.created_at == av.created_at

    def test_returns_new_instance(self) -> None:
        av = _avatar()
        result = apply_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result is not av


# ---------------------------------------------------------------------------
# time_until_critical
# ---------------------------------------------------------------------------


class TestTimeUntilCritical:
    def test_full_meter_returns_positive_seconds(self) -> None:
        seconds = time_until_critical(1.0, _PROD_CONFIG.hunger_rate)
        assert seconds > 0.0

    def test_meter_at_threshold_returns_zero(self) -> None:
        assert time_until_critical(0.2, _PROD_CONFIG.hunger_rate) == 0.0

    def test_meter_below_threshold_returns_zero(self) -> None:
        assert time_until_critical(0.1, _PROD_CONFIG.hunger_rate) == 0.0

    def test_zero_rate_returns_zero(self) -> None:
        assert time_until_critical(1.0, 0.0) == 0.0

    def test_custom_threshold(self) -> None:
        secs = time_until_critical(
            1.0, _PROD_CONFIG.hunger_rate, critical_threshold=0.5
        )
        secs_default = time_until_critical(1.0, _PROD_CONFIG.hunger_rate)
        # Higher threshold → less time remaining
        assert secs < secs_default

    def test_hunger_critical_in_approximately_6_hours(self) -> None:
        # Full hunger (1.0), rate empties in 8h, threshold at 0.2
        # → (1.0 - 0.2) / rate = 0.8 * 8h = 6.4h
        secs = time_until_critical(1.0, _PROD_CONFIG.hunger_rate)
        assert secs == pytest.approx(6.4 * _ONE_HOUR, rel=1e-6)
