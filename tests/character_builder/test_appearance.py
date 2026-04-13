"""Tests for sender_frenz.character_builder.appearance."""

from uuid import uuid4

import pytest

from sender_frenz.character_builder.appearance import (
    HUNGER_CRITICAL,
    HUNGER_IDEAL_MAX,
    HYGIENE_CRITICAL,
    HYGIENE_IDEAL_MAX,
    AppearanceState,
    _composite_label,
    _hunger_visual,
    _hygiene_visual,
    compute_appearance,
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

_NOW: float = 0.0


def _avatar(
    hunger: float = 1.0,
    hygiene: float = 1.0,
    score: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
    skin_upgrades: tuple[str, ...] = (),
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=_NOW),
        social=SocialState(score=score, vampiric_stage=stage, last_interaction=_NOW),
        level=Level(current=0, skin_upgrades=skin_upgrades, room_upgrades=()),
        created_at=_NOW,
    )


# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------


class TestThresholdConstants:
    def test_hunger_ideal_max(self) -> None:
        assert pytest.approx(0.80) == HUNGER_IDEAL_MAX

    def test_hunger_critical(self) -> None:
        assert pytest.approx(0.20) == HUNGER_CRITICAL

    def test_hygiene_ideal_max(self) -> None:
        assert pytest.approx(0.90) == HYGIENE_IDEAL_MAX

    def test_hygiene_critical(self) -> None:
        assert pytest.approx(0.20) == HYGIENE_CRITICAL


# ---------------------------------------------------------------------------
# _hunger_visual bucketing
# ---------------------------------------------------------------------------


class TestHungerVisual:
    def test_above_ideal_max_is_over_nourished(self) -> None:
        assert _hunger_visual(HUNGER_IDEAL_MAX + 0.01) == "over_nourished"

    def test_at_one_is_over_nourished(self) -> None:
        assert _hunger_visual(1.0) == "over_nourished"

    def test_exactly_ideal_max_is_nourished(self) -> None:
        # Boundary: > HUNGER_IDEAL_MAX is "over_nourished"; == is "nourished"
        assert _hunger_visual(HUNGER_IDEAL_MAX) == "nourished"

    def test_mid_range_is_nourished(self) -> None:
        assert _hunger_visual(0.65) == "nourished"

    def test_just_above_midpoint_is_nourished(self) -> None:
        assert _hunger_visual(0.51) == "nourished"

    def test_at_midpoint_is_hungry(self) -> None:
        # Boundary: > 0.50 is "nourished"; == 0.50 is "hungry"
        assert _hunger_visual(0.50) == "hungry"

    def test_between_critical_and_mid_is_hungry(self) -> None:
        assert _hunger_visual(0.35) == "hungry"

    def test_just_above_critical_is_hungry(self) -> None:
        assert _hunger_visual(HUNGER_CRITICAL + 0.01) == "hungry"

    def test_at_critical_is_starved(self) -> None:
        # Boundary: at or below HUNGER_CRITICAL → "starved"
        assert _hunger_visual(HUNGER_CRITICAL) == "starved"

    def test_below_critical_is_starved(self) -> None:
        assert _hunger_visual(HUNGER_CRITICAL - 0.01) == "starved"

    def test_at_zero_is_starved(self) -> None:
        assert _hunger_visual(0.0) == "starved"


# ---------------------------------------------------------------------------
# _hygiene_visual bucketing
# ---------------------------------------------------------------------------


class TestHygieneVisual:
    def test_above_ideal_max_is_over_scrubbed(self) -> None:
        assert _hygiene_visual(HYGIENE_IDEAL_MAX + 0.01) == "over_scrubbed"

    def test_at_one_is_over_scrubbed(self) -> None:
        assert _hygiene_visual(1.0) == "over_scrubbed"

    def test_exactly_ideal_max_is_clean(self) -> None:
        assert _hygiene_visual(HYGIENE_IDEAL_MAX) == "clean"

    def test_mid_range_is_clean(self) -> None:
        assert _hygiene_visual(0.75) == "clean"

    def test_just_above_midpoint_is_clean(self) -> None:
        assert _hygiene_visual(0.61) == "clean"

    def test_at_midpoint_is_unkempt(self) -> None:
        # Boundary: > 0.60 is "clean"; == 0.60 is "unkempt"
        assert _hygiene_visual(0.60) == "unkempt"

    def test_between_critical_and_mid_is_unkempt(self) -> None:
        assert _hygiene_visual(0.40) == "unkempt"

    def test_just_above_critical_is_unkempt(self) -> None:
        assert _hygiene_visual(HYGIENE_CRITICAL + 0.01) == "unkempt"

    def test_at_critical_is_grimy(self) -> None:
        assert _hygiene_visual(HYGIENE_CRITICAL) == "grimy"

    def test_below_critical_is_grimy(self) -> None:
        assert _hygiene_visual(HYGIENE_CRITICAL - 0.01) == "grimy"

    def test_at_zero_is_grimy(self) -> None:
        assert _hygiene_visual(0.0) == "grimy"


# ---------------------------------------------------------------------------
# _composite_label
# ---------------------------------------------------------------------------


class TestCompositeLabel:
    def test_healthy_no_skin_contains_hunger_and_hygiene(self) -> None:
        label = _composite_label(VampiricStage.NONE, "nourished", "clean", None)
        assert "NOURISHED" in label
        assert "CLEAN" in label

    def test_healthy_no_skin_omits_vampiric_stage(self) -> None:
        label = _composite_label(VampiricStage.NONE, "nourished", "clean", None)
        assert "NONE" not in label

    def test_vampiric_stage_present_when_not_none(self) -> None:
        for stage in (
            VampiricStage.PALLOR,
            VampiricStage.GAUNT,
            VampiricStage.HOLLOW,
            VampiricStage.VAMPIRIC,
        ):
            label = _composite_label(stage, "nourished", "clean", None)
            assert stage.name in label

    def test_skin_slug_present_when_given(self) -> None:
        label = _composite_label(
            VampiricStage.NONE, "nourished", "clean", "torn-canvas"
        )
        assert "TORN CANVAS" in label

    def test_skin_slug_absent_when_none(self) -> None:
        label = _composite_label(VampiricStage.NONE, "nourished", "clean", None)
        # Should not contain any extra slash-separated component beyond the two visuals
        parts = label.split(" / ")
        assert len(parts) == 2

    def test_label_is_uppercase(self) -> None:
        label = _composite_label(
            VampiricStage.NONE, "hungry", "grimy", "patch-protocol"
        )
        assert label == label.upper()

    def test_label_uses_slash_separator(self) -> None:
        label = _composite_label(
            VampiricStage.GAUNT, "hungry", "unkempt", "neon-pallor"
        )
        assert " / " in label

    def test_full_degraded_with_skin_has_four_parts(self) -> None:
        label = _composite_label(
            VampiricStage.VAMPIRIC, "starved", "grimy", "void-adjacent"
        )
        parts = label.split(" / ")
        assert len(parts) == 4

    def test_vampiric_stage_none_no_skin_has_two_parts(self) -> None:
        label = _composite_label(VampiricStage.NONE, "nourished", "clean", None)
        parts = label.split(" / ")
        assert len(parts) == 2

    def test_vampiric_stage_active_no_skin_has_three_parts(self) -> None:
        label = _composite_label(VampiricStage.HOLLOW, "nourished", "clean", None)
        parts = label.split(" / ")
        assert len(parts) == 3

    def test_no_stage_with_skin_has_three_parts(self) -> None:
        label = _composite_label(VampiricStage.NONE, "nourished", "clean", "civic-ruin")
        parts = label.split(" / ")
        assert len(parts) == 3

    def test_hyphen_in_slug_becomes_space(self) -> None:
        label = _composite_label(
            VampiricStage.NONE, "nourished", "clean", "chrome-suture"
        )
        assert "CHROME SUTURE" in label
        assert "CHROME-SUTURE" not in label


# ---------------------------------------------------------------------------
# AppearanceState dataclass
# ---------------------------------------------------------------------------


class TestAppearanceState:
    def test_is_frozen(self) -> None:
        import dataclasses

        state = AppearanceState(
            vampiric_stage=VampiricStage.NONE,
            hunger_visual="nourished",
            hygiene_visual="clean",
            skin_slug=None,
            composite_label="NOURISHED / CLEAN",
        )
        assert dataclasses.is_dataclass(state)
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.skin_slug = "test"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# compute_appearance — return type and field pass-through
# ---------------------------------------------------------------------------


class TestComputeAppearanceReturnType:
    def test_returns_appearance_state(self) -> None:
        av = _avatar()
        assert isinstance(compute_appearance(av), AppearanceState)


class TestComputeAppearanceVampiricStage:
    def test_none_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.NONE)
        assert compute_appearance(av).vampiric_stage is VampiricStage.NONE

    def test_pallor_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.PALLOR)
        assert compute_appearance(av).vampiric_stage is VampiricStage.PALLOR

    def test_gaunt_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.GAUNT)
        assert compute_appearance(av).vampiric_stage is VampiricStage.GAUNT

    def test_hollow_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.HOLLOW)
        assert compute_appearance(av).vampiric_stage is VampiricStage.HOLLOW

    def test_vampiric_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.VAMPIRIC)
        assert compute_appearance(av).vampiric_stage is VampiricStage.VAMPIRIC


class TestComputeAppearanceSkinSlug:
    def test_no_skin_returns_none(self) -> None:
        av = _avatar(skin_upgrades=())
        assert compute_appearance(av).skin_slug is None

    def test_single_skin_returns_slug(self) -> None:
        av = _avatar(skin_upgrades=("torn-canvas",))
        assert compute_appearance(av).skin_slug == "torn-canvas"

    def test_multiple_skins_returns_last(self) -> None:
        av = _avatar(skin_upgrades=("torn-canvas", "patch-protocol", "neon-pallor"))
        assert compute_appearance(av).skin_slug == "neon-pallor"


# ---------------------------------------------------------------------------
# compute_appearance — integration scenarios
# ---------------------------------------------------------------------------


class TestComputeAppearanceIntegration:
    def test_fresh_skeleton_avatar(self) -> None:
        """All meters at 1.0; no skin; NONE stage → over_nourished, over_scrubbed."""
        av = _avatar(hunger=1.0, hygiene=1.0, stage=VampiricStage.NONE)
        result = compute_appearance(av)
        assert result.hunger_visual == "over_nourished"
        assert result.hygiene_visual == "over_scrubbed"
        assert result.vampiric_stage is VampiricStage.NONE
        assert result.skin_slug is None

    def test_fresh_skeleton_composite_label(self) -> None:
        av = _avatar(hunger=1.0, hygiene=1.0, stage=VampiricStage.NONE)
        result = compute_appearance(av)
        assert result.composite_label == "OVER_NOURISHED / OVER_SCRUBBED"

    def test_fully_degraded_with_vampiric_and_skin(self) -> None:
        av = _avatar(
            hunger=0.0,
            hygiene=0.0,
            stage=VampiricStage.VAMPIRIC,
            skin_upgrades=("void-adjacent",),
        )
        result = compute_appearance(av)
        assert result.hunger_visual == "starved"
        assert result.hygiene_visual == "grimy"
        assert result.vampiric_stage is VampiricStage.VAMPIRIC
        assert result.skin_slug == "void-adjacent"

    def test_fully_degraded_composite_label(self) -> None:
        av = _avatar(
            hunger=0.0,
            hygiene=0.0,
            stage=VampiricStage.VAMPIRIC,
            skin_upgrades=("void-adjacent",),
        )
        result = compute_appearance(av)
        assert result.composite_label == "VAMPIRIC / STARVED / GRIMY / VOID ADJACENT"

    def test_mid_state_no_drift_with_skin(self) -> None:
        av = _avatar(
            hunger=0.6,
            hygiene=0.7,
            stage=VampiricStage.NONE,
            skin_upgrades=("civic-ruin",),
        )
        result = compute_appearance(av)
        assert result.hunger_visual == "nourished"
        assert result.hygiene_visual == "clean"
        assert result.composite_label == "NOURISHED / CLEAN / CIVIC RUIN"

    def test_gaunt_hungry_unkempt_no_skin(self) -> None:
        av = _avatar(hunger=0.35, hygiene=0.40, stage=VampiricStage.GAUNT)
        result = compute_appearance(av)
        assert result.hunger_visual == "hungry"
        assert result.hygiene_visual == "unkempt"
        assert result.composite_label == "GAUNT / HUNGRY / UNKEMPT"
