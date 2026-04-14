"""Tests for sender_frenz.game_loop.session."""

import dataclasses
import random
from uuid import uuid4

import pytest

from sender_frenz.character_builder.appearance import AppearanceState
from sender_frenz.common.config import PRODUCTION_PACE
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.quips import default_quip_caller
from sender_frenz.common.types import AvatarId
from sender_frenz.game_loop.session import SessionState, open_session
from sender_frenz.game_loop.tick import _HUNGER_WARNING_THRESHOLD, GameEventKind
from sender_frenz.required_maintenance.needs import NeedsSummary
from sender_frenz.social_maintenance.effects import SocialSummary
from sender_frenz.social_maintenance.history import create_history

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECONDS_PER_HOUR: float = 3600.0
_HUNGER_RATE: float = 1.0 / 8.0  # Meter/hour at PRODUCTION_PACE
_SUSTAIN_SECONDS: float = 4.0 * _SECONDS_PER_HOUR  # LevelConfig base sustain window
_QUIP_CALLER = default_quip_caller(rng=random.Random(0))


def _seconds_to_drop(drop: float, rate_per_hour: float) -> float:
    return (drop / rate_per_hour) * _SECONDS_PER_HOUR


def _avatar(
    hunger: float = 1.0,
    hygiene: float = 1.0,
    social: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
    now: float = 0.0,
) -> Avatar:
    """Avatar whose timestamps are all set to *now* so elapsed = 0 by default."""
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=now),
        social=SocialState(score=social, vampiric_stage=stage, last_interaction=now),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# SessionState dataclass
# ---------------------------------------------------------------------------


class TestSessionState:
    def test_is_frozen(self) -> None:
        av = _avatar()
        ss = SessionState(
            avatar=av,
            needs_summary=NeedsSummary(
                hunger=1.0,
                hygiene=1.0,
                hungry=False,
                dirty=False,
                over_nourished=False,
                over_scrubbed=False,
            ),
            social_summary=SocialSummary(
                score=1.0,
                vampiric_stage=VampiricStage.NONE,
                is_isolated=False,
                is_thriving=True,
                stage_label="NOMINAL",
            ),
            appearance=AppearanceState(
                vampiric_stage=VampiricStage.NONE,
                hunger_visual="nourished",
                hygiene_visual="clean",
                skin_slug=None,
                composite_label="NOURISHED / CLEAN",
            ),
            level_up_available=False,
            events=(),
            quips=("quip",),
        )
        assert dataclasses.is_dataclass(ss)
        with pytest.raises(dataclasses.FrozenInstanceError):
            ss.level_up_available = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# open_session — decay applied
# ---------------------------------------------------------------------------


class TestOpenSessionDecay:
    def test_applies_decay_to_avatar(self) -> None:
        """Meters decrease when elapsed time is positive."""
        now = 0.0
        av = _avatar(hunger=1.0, now=now)
        elapsed = _SECONDS_PER_HOUR
        result = open_session(
            av, create_history(), None, elapsed, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.avatar.needs.hunger < 1.0

    def test_no_decay_when_zero_elapsed(self) -> None:
        now = 500.0
        av = _avatar(hunger=0.8, now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.avatar.needs.hunger == pytest.approx(0.8)

    def test_avatar_timestamps_advanced_to_now(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        later = _SECONDS_PER_HOUR
        result = open_session(
            av, create_history(), None, later, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.avatar.needs.last_updated == pytest.approx(later)
        assert result.avatar.social.last_interaction == pytest.approx(later)

    def test_returns_session_state_instance(self) -> None:
        av = _avatar()
        result = open_session(
            av, create_history(), None, 0.0, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert isinstance(result, SessionState)


# ---------------------------------------------------------------------------
# open_session — status summaries reflect post-tick state
# ---------------------------------------------------------------------------


class TestOpenSessionSummaries:
    def test_needs_summary_reflects_post_tick_avatar(self) -> None:
        now = 0.0
        av = _avatar(hunger=0.10, now=now)  # already hungry/critical
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert isinstance(result.needs_summary, NeedsSummary)
        assert result.needs_summary.hungry is True

    def test_social_summary_reflects_post_tick_avatar(self) -> None:
        now = 0.0
        av = _avatar(social=0.10, now=now)  # isolated
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert isinstance(result.social_summary, SocialSummary)
        assert result.social_summary.is_isolated is True

    def test_appearance_reflects_post_tick_avatar(self) -> None:
        now = 0.0
        av = _avatar(hunger=1.0, hygiene=1.0, social=1.0, now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert isinstance(result.appearance, AppearanceState)


# ---------------------------------------------------------------------------
# open_session — level-up eligibility
# ---------------------------------------------------------------------------


class TestOpenSessionLevelUp:
    def test_level_up_false_when_sustained_since_none(self) -> None:
        now = 0.0
        av = _avatar(hunger=0.9, hygiene=0.9, social=0.9, now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.level_up_available is False

    def test_level_up_true_when_threshold_sustained(self) -> None:
        now = 0.0
        av = _avatar(hunger=0.9, hygiene=0.9, social=0.9, now=now)
        # sustained_since = 4 hours ago
        sustained_since = now - _SUSTAIN_SECONDS
        result = open_session(
            av, create_history(), sustained_since, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.level_up_available is True

    def test_level_up_false_when_not_sustained_long_enough(self) -> None:
        now = 0.0
        av = _avatar(hunger=0.9, hygiene=0.9, social=0.9, now=now)
        # sustained for only 1 hour (need 4)
        sustained_since = now - _SECONDS_PER_HOUR
        result = open_session(
            av, create_history(), sustained_since, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.level_up_available is False

    def test_level_up_false_when_health_below_threshold(self) -> None:
        now = 0.0
        av = _avatar(
            hunger=0.5, hygiene=0.5, social=0.5, now=now
        )  # combined = 0.5 < 0.75
        sustained_since = now - _SUSTAIN_SECONDS
        result = open_session(
            av, create_history(), sustained_since, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.level_up_available is False


# ---------------------------------------------------------------------------
# open_session — LEVEL_UP_READY event
# ---------------------------------------------------------------------------


class TestOpenSessionLevelUpEvent:
    def test_level_up_ready_in_events_when_eligible(self) -> None:
        now = 0.0
        av = _avatar(hunger=0.9, hygiene=0.9, social=0.9, now=now)
        sustained_since = now - _SUSTAIN_SECONDS
        result = open_session(
            av, create_history(), sustained_since, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert any(e.kind is GameEventKind.LEVEL_UP_READY for e in result.events)

    def test_level_up_ready_not_in_events_when_not_eligible(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert all(e.kind is not GameEventKind.LEVEL_UP_READY for e in result.events)

    def test_level_up_ready_event_carries_now_timestamp(self) -> None:
        now = 999.0
        av = _avatar(hunger=0.9, hygiene=0.9, social=0.9, now=now)
        sustained_since = now - _SUSTAIN_SECONDS
        result = open_session(
            av, create_history(), sustained_since, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        ready_events = [
            e for e in result.events if e.kind is GameEventKind.LEVEL_UP_READY
        ]
        assert len(ready_events) == 1
        assert ready_events[0].timestamp == pytest.approx(now)


# ---------------------------------------------------------------------------
# open_session — quips
# ---------------------------------------------------------------------------


class TestOpenSessionQuips:
    def test_login_quip_always_present(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert len(result.quips) >= 1
        assert isinstance(result.quips[0], str)
        assert len(result.quips[0]) > 0

    def test_threshold_event_produces_quip(self) -> None:
        """HUNGER_WARNING event produces a second quip after LOGIN."""
        above = _HUNGER_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HUNGER_RATE)
        av = _avatar(hunger=above)
        result = open_session(
            av, create_history(), None, elapsed, PRODUCTION_PACE, _QUIP_CALLER
        )
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING in kinds
        assert len(result.quips) == 2  # LOGIN + HUNGER_WARNING

    def test_no_quip_for_level_up_ready_event(self) -> None:
        """LEVEL_UP_READY event has no quip trigger; only LOGIN quip present."""
        now = 0.0
        av = _avatar(hunger=0.9, hygiene=0.9, social=0.9, now=now)
        sustained_since = now - _SUSTAIN_SECONDS
        result = open_session(
            av, create_history(), sustained_since, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.level_up_available is True
        assert any(e.kind is GameEventKind.LEVEL_UP_READY for e in result.events)
        # Only the LOGIN quip; LEVEL_UP_READY has no mapped trigger
        assert len(result.quips) == 1

    def test_no_quip_for_vampiric_advance_event(self) -> None:
        """VAMPIRIC_ADVANCE event has no quip trigger; only LOGIN quip present."""
        elapsed = 12.0 * _SECONDS_PER_HOUR + 1.0
        # Set needs timestamps to elapsed so needs have zero elapsed — only
        # social advances (last_interaction=0.0 → social_elapsed = elapsed).
        av = Avatar(
            id=AvatarId(uuid4()),
            needs=NeedState(hunger=1.0, hygiene=1.0, last_updated=elapsed),
            social=SocialState(
                score=0.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
            ),
            level=Level(current=0, skin_upgrades=(), room_upgrades=()),
            created_at=0.0,
        )
        result = open_session(
            av, create_history(), None, elapsed, PRODUCTION_PACE, _QUIP_CALLER
        )
        kinds = {e.kind for e in result.events}
        assert GameEventKind.VAMPIRIC_ADVANCE in kinds
        assert len(result.quips) == 1  # only LOGIN

    def test_quips_are_non_empty_strings(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        for quip in result.quips:
            assert isinstance(quip, str)
            assert len(quip) > 0

    def test_quips_is_tuple(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert isinstance(result.quips, tuple)


# ---------------------------------------------------------------------------
# open_session — events passthrough
# ---------------------------------------------------------------------------


class TestOpenSessionEvents:
    def test_tick_events_included_in_session_events(self) -> None:
        above = _HUNGER_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HUNGER_RATE)
        av = _avatar(hunger=above)
        result = open_session(
            av, create_history(), None, elapsed, PRODUCTION_PACE, _QUIP_CALLER
        )
        tick_kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING in tick_kinds

    def test_events_is_tuple(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert isinstance(result.events, tuple)

    def test_no_events_for_fresh_avatar_no_elapsed(self) -> None:
        now = 0.0
        av = _avatar(now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )
        assert result.events == ()


# ---------------------------------------------------------------------------
# open_session — integration scenarios
# ---------------------------------------------------------------------------


class TestOpenSessionIntegration:
    def test_fresh_avatar_healthy_state(self) -> None:
        """All meters at 1.0, zero elapsed → healthy summaries, no events."""
        now = 0.0
        av = _avatar(hunger=1.0, hygiene=1.0, social=1.0, now=now)
        result = open_session(
            av, create_history(), None, now, PRODUCTION_PACE, _QUIP_CALLER
        )

        assert result.needs_summary.hungry is False
        assert result.needs_summary.dirty is False
        assert result.social_summary.is_isolated is False
        assert result.level_up_available is False
        assert result.events == ()
        assert len(result.quips) == 1  # only LOGIN

    def test_neglected_avatar_produces_multiple_events(self) -> None:
        """Long absence with low meters produces threshold events and quips."""
        now = 0.0
        av = _avatar(hunger=0.51, hygiene=0.61, social=1.0, now=now)
        # 10 hours: crosses hunger warning (0.50) and hygiene warning (0.60)
        elapsed = 10.0 * _SECONDS_PER_HOUR
        result = open_session(
            av, create_history(), None, elapsed, PRODUCTION_PACE, _QUIP_CALLER
        )

        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING in kinds
        assert GameEventKind.HYGIENE_WARNING in kinds
        assert len(result.quips) > 1  # LOGIN + warning quips
