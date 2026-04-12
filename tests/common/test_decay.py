"""Tests for sender_frenz.common.decay."""

from uuid import uuid4

import pytest

from sender_frenz.common.config import PRODUCTION_PACE, TEST_PACE, GamePace
from sender_frenz.common.decay import (
    Decay,
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


def _avatar(
    hunger: float = 1.0,
    hygiene: float = 1.0,
    score: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=0.0),
        social=SocialState(score=score, vampiric_stage=stage, last_interaction=0.0),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# Decay / DecayConfig construction
# ---------------------------------------------------------------------------


class TestDecayDataclass:
    def test_fields_stored(self) -> None:
        def always(av: Avatar) -> bool:
            return True

        d = Decay(name="test", meter="hunger", rate_per_hour=0.5, condition=always)
        assert d.name == "test"
        assert d.meter == "hunger"
        assert d.rate_per_hour == 0.5
        assert d.condition is always


# ---------------------------------------------------------------------------
# DecayConfig.from_pace
# ---------------------------------------------------------------------------


class TestDecayConfigFromPace:
    def test_production_rates_match_documented_values(self) -> None:
        cfg = DecayConfig.from_pace(PRODUCTION_PACE)
        av = _avatar()
        assert cfg.effective_rate(av, "hunger") == pytest.approx(1.0 / 8.0)
        assert cfg.effective_rate(av, "hygiene") == pytest.approx(1.0 / 12.0)
        assert cfg.effective_rate(av, "social") == pytest.approx(1.0 / 24.0)
        assert cfg.vampiric_advance_hours == pytest.approx(12.0)
        assert cfg.vampiric_retreat_rate == pytest.approx(0.5)

    def test_test_pace_rates_are_720x_production(self) -> None:
        av = _avatar()
        prod = DecayConfig.from_pace(PRODUCTION_PACE)
        test = DecayConfig.from_pace(TEST_PACE)
        assert test.effective_rate(av, "hunger") == pytest.approx(
            prod.effective_rate(av, "hunger") * 720.0
        )
        assert test.effective_rate(av, "hygiene") == pytest.approx(
            prod.effective_rate(av, "hygiene") * 720.0
        )
        assert test.effective_rate(av, "social") == pytest.approx(
            prod.effective_rate(av, "social") * 720.0
        )
        assert test.vampiric_advance_hours == pytest.approx(
            prod.vampiric_advance_hours / 720.0
        )
        assert test.vampiric_retreat_rate == pytest.approx(
            prod.vampiric_retreat_rate * 720.0
        )

    def test_custom_pace_scales_correctly(self) -> None:
        av = _avatar()
        cfg = DecayConfig.from_pace(GamePace(time_scale=2.0))
        assert cfg.effective_rate(av, "hunger") == pytest.approx((1.0 / 8.0) * 2.0)

    def test_base_decays_tuple_has_three_entries(self) -> None:
        cfg = DecayConfig.from_pace(PRODUCTION_PACE)
        assert len(cfg.decays) == 3

    def test_extra_decays_appended(self) -> None:
        def always(av: Avatar) -> bool:
            return True

        extra = Decay(name="bonus", meter="hunger", rate_per_hour=1.0, condition=always)
        cfg = DecayConfig.from_pace(PRODUCTION_PACE, extra_decays=(extra,))
        assert len(cfg.decays) == 4


# ---------------------------------------------------------------------------
# DecayConfig.effective_rate — composability
# ---------------------------------------------------------------------------


class TestEffectiveRate:
    def test_inactive_condition_excluded_from_rate(self) -> None:
        def never(av: Avatar) -> bool:
            return False

        extra = Decay(name="never", meter="hunger", rate_per_hour=99.0, condition=never)
        cfg = DecayConfig.from_pace(PRODUCTION_PACE, extra_decays=(extra,))
        av = _avatar(hunger=1.0)
        base_rate = DecayConfig.from_pace(PRODUCTION_PACE).effective_rate(av, "hunger")
        # The extra 99.0 rule is inactive; only base rate should apply.
        assert cfg.effective_rate(av, "hunger") == pytest.approx(base_rate)

    def test_active_condition_adds_to_rate(self) -> None:
        def always(av: Avatar) -> bool:
            return True

        extra = Decay(name="bonus", meter="hunger", rate_per_hour=1.0, condition=always)
        cfg = DecayConfig.from_pace(PRODUCTION_PACE, extra_decays=(extra,))
        av = _avatar(hunger=1.0)
        base_rate = DecayConfig.from_pace(PRODUCTION_PACE).effective_rate(av, "hunger")
        assert cfg.effective_rate(av, "hunger") == pytest.approx(base_rate + 1.0)

    def test_different_meter_not_included(self) -> None:
        av = _avatar()
        # Querying "hygiene" should not include the "hunger" base decay.
        rate = _PROD_CONFIG.effective_rate(av, "hygiene")
        assert rate == pytest.approx(1.0 / 12.0)


# ---------------------------------------------------------------------------
# apply_need_decay
# ---------------------------------------------------------------------------


class TestApplyNeedDecay:
    def test_zero_elapsed_returns_same_values(self) -> None:
        av = _avatar(hunger=0.8, hygiene=0.6)
        result = apply_need_decay(av, 0.0, _PROD_CONFIG)
        assert result.hunger == pytest.approx(0.8)
        assert result.hygiene == pytest.approx(0.6)

    def test_hunger_decreases_over_time(self) -> None:
        av = _avatar(hunger=1.0)
        result = apply_need_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result.hunger < 1.0

    def test_hygiene_decreases_over_time(self) -> None:
        av = _avatar(hygiene=1.0)
        result = apply_need_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result.hygiene < 1.0

    def test_hunger_empties_in_8_hours(self) -> None:
        av = _avatar(hunger=1.0)
        result = apply_need_decay(av, 8 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hunger == pytest.approx(0.0, abs=1e-9)

    def test_hygiene_empties_in_12_hours(self) -> None:
        av = _avatar(hygiene=1.0)
        result = apply_need_decay(av, 12 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hygiene == pytest.approx(0.0, abs=1e-9)

    def test_hunger_clamps_at_zero(self) -> None:
        av = _avatar(hunger=0.1)
        result = apply_need_decay(av, 100 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hunger == 0.0

    def test_hygiene_clamps_at_zero(self) -> None:
        av = _avatar(hygiene=0.1)
        result = apply_need_decay(av, 100 * _ONE_HOUR, _PROD_CONFIG)
        assert result.hygiene == 0.0

    def test_last_updated_advances(self) -> None:
        av = _avatar()
        result = apply_need_decay(av, 500.0, _PROD_CONFIG)
        assert result.last_updated == pytest.approx(500.0)

    def test_returns_new_instance(self) -> None:
        av = _avatar()
        result = apply_need_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result is not av.needs

    def test_conditional_decay_doubles_rate_when_active(self) -> None:
        # Extra rule that always fires adds base hunger rate → double drain.
        def always(a: Avatar) -> bool:
            return True

        extra = Decay(
            name="double",
            meter="hunger",
            rate_per_hour=1.0 / 8.0,
            condition=always,
        )
        cfg = DecayConfig.from_pace(PRODUCTION_PACE, extra_decays=(extra,))
        av = _avatar(hunger=1.0)
        result = apply_need_decay(av, 4 * _ONE_HOUR, cfg)
        # At double rate, 4 h empties hunger (2 x 0.125 x 4 = 1.0).
        assert result.hunger == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# apply_social_decay
# ---------------------------------------------------------------------------


class TestApplySocialDecay:
    def test_zero_elapsed_returns_same_values(self) -> None:
        av = _avatar(score=0.8)
        result = apply_social_decay(av, 0.0, _PROD_CONFIG)
        assert result.score == pytest.approx(0.8)
        assert result.vampiric_stage == VampiricStage.NONE

    def test_score_decreases_over_time(self) -> None:
        av = _avatar(score=1.0)
        result = apply_social_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result.score < 1.0

    def test_social_empties_in_24_hours(self) -> None:
        av = _avatar(score=1.0)
        result = apply_social_decay(av, 24 * _ONE_HOUR, _PROD_CONFIG)
        assert result.score == pytest.approx(0.0, abs=1e-9)

    def test_score_clamps_at_zero(self) -> None:
        av = _avatar(score=0.1)
        result = apply_social_decay(av, 100 * _ONE_HOUR, _PROD_CONFIG)
        assert result.score == 0.0

    def test_vampiric_stage_advances_when_score_zero(self) -> None:
        # score=0, elapsed = 2 x vampiric_advance_hours -> 2 stage advances
        advance_secs = _PROD_CONFIG.vampiric_advance_hours * _ONE_HOUR * 2
        av = _avatar(score=0.0, stage=VampiricStage.NONE)
        result = apply_social_decay(av, advance_secs, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.GAUNT

    def test_vampiric_stage_clamps_at_vampiric(self) -> None:
        av = _avatar(score=0.0, stage=VampiricStage.HOLLOW)
        result = apply_social_decay(av, 1000 * _ONE_HOUR, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.VAMPIRIC

    def test_vampiric_stage_retreats_when_score_positive(self) -> None:
        # retreat_rate=0.5 stages/hour; 2 hours → 1 stage retreat
        av = _avatar(score=0.5, stage=VampiricStage.GAUNT)
        result = apply_social_decay(av, 2 * _ONE_HOUR, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.PALLOR

    def test_no_retreat_below_none(self) -> None:
        # score=0.5 decays at 1/24 Meter/hour; after 1 h score ≈ 0.458 (still > 0)
        # retreat logic fires but stage is already NONE — must clamp at NONE.
        av = _avatar(score=0.5, stage=VampiricStage.NONE)
        result = apply_social_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result.vampiric_stage == VampiricStage.NONE

    def test_last_interaction_advances(self) -> None:
        av = _avatar()
        result = apply_social_decay(av, 300.0, _PROD_CONFIG)
        assert result.last_interaction == pytest.approx(300.0)

    def test_returns_new_instance(self) -> None:
        av = _avatar()
        result = apply_social_decay(av, _ONE_HOUR, _PROD_CONFIG)
        assert result is not av.social


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
        av = _avatar(hunger=1.0)
        rate = _PROD_CONFIG.effective_rate(av, "hunger")
        seconds = time_until_critical(1.0, rate)
        assert seconds > 0.0

    def test_meter_at_threshold_returns_zero(self) -> None:
        av = _avatar(hunger=1.0)
        rate = _PROD_CONFIG.effective_rate(av, "hunger")
        assert time_until_critical(0.2, rate) == 0.0

    def test_meter_below_threshold_returns_zero(self) -> None:
        av = _avatar(hunger=1.0)
        rate = _PROD_CONFIG.effective_rate(av, "hunger")
        assert time_until_critical(0.1, rate) == 0.0

    def test_zero_rate_returns_zero(self) -> None:
        assert time_until_critical(1.0, 0.0) == 0.0

    def test_custom_threshold(self) -> None:
        av = _avatar(hunger=1.0)
        rate = _PROD_CONFIG.effective_rate(av, "hunger")
        secs = time_until_critical(1.0, rate, critical_threshold=0.5)
        secs_default = time_until_critical(1.0, rate)
        # Higher threshold → less time remaining.
        assert secs < secs_default

    def test_hunger_critical_in_approximately_6_point_4_hours(self) -> None:
        # Full hunger (1.0), rate empties in 8 h, threshold at 0.2
        # -> (1.0 - 0.2) / rate = 0.8 x 8 h = 6.4 h
        av = _avatar(hunger=1.0)
        rate = _PROD_CONFIG.effective_rate(av, "hunger")
        secs = time_until_critical(1.0, rate)
        assert secs == pytest.approx(6.4 * _ONE_HOUR, rel=1e-6)
