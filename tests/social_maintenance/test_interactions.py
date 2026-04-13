"""Tests for sender_frenz.social_maintenance.interactions."""

import random
from uuid import uuid4

import pytest

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.quips import QuipTrigger, default_quip_caller
from sender_frenz.common.types import AvatarId
from sender_frenz.social_maintenance.interactions import (
    CHAT_SCORE_BOOST,
    GIFT_SCORE_BOOST,
    VISIT_SCORE_BOOST,
    InteractionKind,
    InteractionResult,
    interact,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FIXED_QUIP_CALLER = default_quip_caller(rng=random.Random(0))
_NOW = 1000.0


def _avatar(score: float = 0.5) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
        social=SocialState(
            score=score,
            vampiric_stage=VampiricStage.NONE,
            last_interaction=0.0,
        ),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestInteractionConstants:
    def test_visit_score_boost(self) -> None:
        assert pytest.approx(0.25) == VISIT_SCORE_BOOST

    def test_gift_score_boost(self) -> None:
        assert pytest.approx(0.15) == GIFT_SCORE_BOOST

    def test_chat_score_boost(self) -> None:
        assert pytest.approx(0.05) == CHAT_SCORE_BOOST

    def test_visit_is_largest_boost(self) -> None:
        assert VISIT_SCORE_BOOST > GIFT_SCORE_BOOST > CHAT_SCORE_BOOST


# ---------------------------------------------------------------------------
# InteractionKind enum
# ---------------------------------------------------------------------------


class TestInteractionKind:
    def test_all_kinds_defined(self) -> None:
        names = {k.name for k in InteractionKind}
        assert names == {"VISIT", "GIFT", "CHAT"}

    def test_kind_values_are_strings(self) -> None:
        for kind in InteractionKind:
            assert isinstance(kind.value, str)


# ---------------------------------------------------------------------------
# interact — score boosts
# ---------------------------------------------------------------------------


class TestInteractScoreBoost:
    def test_visit_boosts_score(self) -> None:
        av = _avatar(score=0.3)
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(0.3 + VISIT_SCORE_BOOST)

    def test_gift_boosts_score(self) -> None:
        av = _avatar(score=0.3)
        result = interact(av, InteractionKind.GIFT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(0.3 + GIFT_SCORE_BOOST)

    def test_chat_boosts_score(self) -> None:
        av = _avatar(score=0.3)
        result = interact(av, InteractionKind.CHAT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(0.3 + CHAT_SCORE_BOOST)

    def test_score_clamped_at_one_for_visit(self) -> None:
        av = _avatar(score=0.9)
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(1.0)

    def test_score_clamped_at_one_for_gift(self) -> None:
        av = _avatar(score=0.95)
        result = interact(av, InteractionKind.GIFT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(1.0)

    def test_score_clamped_at_one_for_chat(self) -> None:
        av = _avatar(score=0.99)
        result = interact(av, InteractionKind.CHAT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(1.0)

    def test_score_already_at_one_stays_at_one(self) -> None:
        av = _avatar(score=1.0)
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# interact — timestamp
# ---------------------------------------------------------------------------


class TestInteractTimestamp:
    def test_last_interaction_updated_to_now(self) -> None:
        av = _avatar()
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.last_interaction == pytest.approx(_NOW)

    def test_different_now_values_recorded(self) -> None:
        av = _avatar()
        r1 = interact(av, InteractionKind.CHAT, 500.0, _FIXED_QUIP_CALLER)
        r2 = interact(av, InteractionKind.CHAT, 999.0, _FIXED_QUIP_CALLER)
        assert r1.avatar.social.last_interaction == pytest.approx(500.0)
        assert r2.avatar.social.last_interaction == pytest.approx(999.0)


# ---------------------------------------------------------------------------
# interact — unchanged fields
# ---------------------------------------------------------------------------


class TestInteractPreservesState:
    def test_vampiric_stage_unchanged(self) -> None:
        av = Avatar(
            id=AvatarId(uuid4()),
            needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=0.0),
            social=SocialState(
                score=0.1,
                vampiric_stage=VampiricStage.GAUNT,
                last_interaction=0.0,
            ),
            level=Level(current=0, skin_upgrades=(), room_upgrades=()),
            created_at=0.0,
        )
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.social.vampiric_stage is VampiricStage.GAUNT

    def test_needs_unchanged(self) -> None:
        av = _avatar()
        result = interact(av, InteractionKind.GIFT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.needs == av.needs

    def test_level_unchanged(self) -> None:
        av = _avatar()
        result = interact(av, InteractionKind.CHAT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.level == av.level

    def test_id_preserved(self) -> None:
        av = _avatar()
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.id == av.id

    def test_created_at_preserved(self) -> None:
        av = _avatar()
        result = interact(av, InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert result.avatar.created_at == pytest.approx(av.created_at)


# ---------------------------------------------------------------------------
# interact — quip triggers
# ---------------------------------------------------------------------------


class TestInteractQuipTriggers:
    def _recording_caller(self) -> tuple[list[QuipTrigger], object]:
        triggered: list[QuipTrigger] = []

        def caller(t: QuipTrigger) -> str:
            triggered.append(t)
            return "quip"

        return triggered, caller

    def test_visit_fires_visit_trigger(self) -> None:
        triggered, caller = self._recording_caller()
        interact(_avatar(), InteractionKind.VISIT, _NOW, caller)  # type: ignore[arg-type]
        assert triggered == [QuipTrigger.VISIT]

    def test_gift_fires_gift_trigger(self) -> None:
        triggered, caller = self._recording_caller()
        interact(_avatar(), InteractionKind.GIFT, _NOW, caller)  # type: ignore[arg-type]
        assert triggered == [QuipTrigger.GIFT]

    def test_chat_fires_chat_trigger(self) -> None:
        triggered, caller = self._recording_caller()
        interact(_avatar(), InteractionKind.CHAT, _NOW, caller)  # type: ignore[arg-type]
        assert triggered == [QuipTrigger.CHAT]

    def test_quip_is_non_empty_string(self) -> None:
        result = interact(_avatar(), InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert isinstance(result.quip, str)
        assert len(result.quip) > 0


# ---------------------------------------------------------------------------
# InteractionResult
# ---------------------------------------------------------------------------


class TestInteractionResult:
    def test_returns_interaction_result(self) -> None:
        result = interact(_avatar(), InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert isinstance(result, InteractionResult)

    def test_is_frozen(self) -> None:
        import dataclasses

        result = interact(_avatar(), InteractionKind.VISIT, _NOW, _FIXED_QUIP_CALLER)
        assert dataclasses.is_dataclass(result)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.quip = "x"  # type: ignore[misc]
