"""Tests for sender_frenz.social_maintenance.effects."""

import dataclasses
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
from sender_frenz.social_maintenance.effects import (
    _STAGE_LABELS,
    ISOLATION_THRESHOLD,
    THRIVING_THRESHOLD,
    SocialSummary,
    social_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _avatar(
    score: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
        social=SocialState(score=score, vampiric_stage=stage, last_interaction=0.0),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------


class TestThresholdConstants:
    def test_isolation_threshold(self) -> None:
        assert pytest.approx(0.20) == ISOLATION_THRESHOLD

    def test_thriving_threshold(self) -> None:
        assert pytest.approx(0.75) == THRIVING_THRESHOLD

    def test_isolation_below_thriving(self) -> None:
        assert ISOLATION_THRESHOLD < THRIVING_THRESHOLD


# ---------------------------------------------------------------------------
# Stage labels
# ---------------------------------------------------------------------------


class TestStageLabels:
    def test_all_stages_have_labels(self) -> None:
        for stage in VampiricStage:
            assert stage in _STAGE_LABELS

    def test_none_label(self) -> None:
        assert _STAGE_LABELS[VampiricStage.NONE] == "NOMINAL"

    def test_pallor_label(self) -> None:
        assert _STAGE_LABELS[VampiricStage.PALLOR] == "PALLOR ONSET"

    def test_gaunt_label(self) -> None:
        assert _STAGE_LABELS[VampiricStage.GAUNT] == "STRUCTURAL DRIFT"

    def test_hollow_label(self) -> None:
        assert _STAGE_LABELS[VampiricStage.HOLLOW] == "OCULAR VOID"

    def test_vampiric_label(self) -> None:
        assert _STAGE_LABELS[VampiricStage.VAMPIRIC] == "FULL EXPRESSION"

    def test_all_labels_uppercase(self) -> None:
        for label in _STAGE_LABELS.values():
            assert label == label.upper()


# ---------------------------------------------------------------------------
# SocialSummary dataclass
# ---------------------------------------------------------------------------


class TestSocialSummaryDataclass:
    def test_is_frozen(self) -> None:
        summary = SocialSummary(
            score=1.0,
            vampiric_stage=VampiricStage.NONE,
            is_isolated=False,
            is_thriving=True,
            stage_label="NOMINAL",
        )
        assert dataclasses.is_dataclass(summary)
        with pytest.raises(dataclasses.FrozenInstanceError):
            summary.score = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# social_summary — is_isolated
# ---------------------------------------------------------------------------


class TestSocialSummaryIsolated:
    def test_isolated_at_threshold(self) -> None:
        av = _avatar(score=ISOLATION_THRESHOLD)
        assert social_summary(av).is_isolated is True

    def test_isolated_below_threshold(self) -> None:
        av = _avatar(score=ISOLATION_THRESHOLD - 0.01)
        assert social_summary(av).is_isolated is True

    def test_isolated_at_zero(self) -> None:
        av = _avatar(score=0.0)
        assert social_summary(av).is_isolated is True

    def test_not_isolated_above_threshold(self) -> None:
        av = _avatar(score=ISOLATION_THRESHOLD + 0.01)
        assert social_summary(av).is_isolated is False

    def test_not_isolated_at_full(self) -> None:
        av = _avatar(score=1.0)
        assert social_summary(av).is_isolated is False


# ---------------------------------------------------------------------------
# social_summary — is_thriving
# ---------------------------------------------------------------------------


class TestSocialSummaryThriving:
    def test_thriving_above_threshold(self) -> None:
        av = _avatar(score=THRIVING_THRESHOLD + 0.01)
        assert social_summary(av).is_thriving is True

    def test_thriving_at_full(self) -> None:
        av = _avatar(score=1.0)
        assert social_summary(av).is_thriving is True

    def test_not_thriving_at_threshold(self) -> None:
        # Boundary: strictly above threshold required
        av = _avatar(score=THRIVING_THRESHOLD)
        assert social_summary(av).is_thriving is False

    def test_not_thriving_below_threshold(self) -> None:
        av = _avatar(score=THRIVING_THRESHOLD - 0.01)
        assert social_summary(av).is_thriving is False

    def test_not_thriving_at_zero(self) -> None:
        av = _avatar(score=0.0)
        assert social_summary(av).is_thriving is False


# ---------------------------------------------------------------------------
# social_summary — stage label and vampiric stage passthrough
# ---------------------------------------------------------------------------


class TestSocialSummaryStage:
    def test_none_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.NONE)
        summary = social_summary(av)
        assert summary.vampiric_stage is VampiricStage.NONE
        assert summary.stage_label == "NOMINAL"

    def test_pallor_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.PALLOR)
        summary = social_summary(av)
        assert summary.vampiric_stage is VampiricStage.PALLOR
        assert summary.stage_label == "PALLOR ONSET"

    def test_gaunt_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.GAUNT)
        summary = social_summary(av)
        assert summary.vampiric_stage is VampiricStage.GAUNT
        assert summary.stage_label == "STRUCTURAL DRIFT"

    def test_hollow_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.HOLLOW)
        summary = social_summary(av)
        assert summary.vampiric_stage is VampiricStage.HOLLOW
        assert summary.stage_label == "OCULAR VOID"

    def test_vampiric_stage_passes_through(self) -> None:
        av = _avatar(stage=VampiricStage.VAMPIRIC)
        summary = social_summary(av)
        assert summary.vampiric_stage is VampiricStage.VAMPIRIC
        assert summary.stage_label == "FULL EXPRESSION"


# ---------------------------------------------------------------------------
# social_summary — score passthrough
# ---------------------------------------------------------------------------


class TestSocialSummaryScore:
    def test_score_passed_through(self) -> None:
        av = _avatar(score=0.42)
        assert social_summary(av).score == pytest.approx(0.42)


# ---------------------------------------------------------------------------
# social_summary — integration scenarios
# ---------------------------------------------------------------------------


class TestSocialSummaryIntegration:
    def test_fresh_avatar(self) -> None:
        """score=1.0, NONE → thriving, not isolated, NOMINAL."""
        av = _avatar(score=1.0, stage=VampiricStage.NONE)
        summary = social_summary(av)
        assert summary.is_thriving is True
        assert summary.is_isolated is False
        assert summary.stage_label == "NOMINAL"
        assert summary.vampiric_stage is VampiricStage.NONE

    def test_isolated_vampiric_avatar(self) -> None:
        """score=0.0, VAMPIRIC → isolated, not thriving, FULL EXPRESSION."""
        av = _avatar(score=0.0, stage=VampiricStage.VAMPIRIC)
        summary = social_summary(av)
        assert summary.is_isolated is True
        assert summary.is_thriving is False
        assert summary.stage_label == "FULL EXPRESSION"
        assert summary.vampiric_stage is VampiricStage.VAMPIRIC

    def test_mid_range_neither_isolated_nor_thriving(self) -> None:
        av = _avatar(score=0.5, stage=VampiricStage.PALLOR)
        summary = social_summary(av)
        assert summary.is_isolated is False
        assert summary.is_thriving is False
        assert summary.stage_label == "PALLOR ONSET"

    def test_returns_social_summary_instance(self) -> None:
        assert isinstance(social_summary(_avatar()), SocialSummary)
