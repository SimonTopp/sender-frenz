"""Tests for sender_frenz.game_loop.tick."""

import dataclasses
from uuid import uuid4

import pytest

from sender_frenz.common.config import PRODUCTION_PACE
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId
from sender_frenz.game_loop.tick import (
    _HUNGER_CRITICAL_THRESHOLD,
    _HUNGER_WARNING_THRESHOLD,
    _HYGIENE_CRITICAL_THRESHOLD,
    _HYGIENE_WARNING_THRESHOLD,
    _SOCIAL_CRITICAL_THRESHOLD,
    _SOCIAL_WARNING_THRESHOLD,
    GameEvent,
    GameEventKind,
    TickResult,
    process_tick,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECONDS_PER_HOUR: float = 3600.0

# PRODUCTION_PACE base rates (Meter/hour)
_HUNGER_RATE: float = 1.0 / 8.0
_HYGIENE_RATE: float = 1.0 / 12.0
_SOCIAL_RATE: float = 1.0 / 24.0
_VAMPIRIC_ADVANCE_HOURS: float = 12.0
_VAMPIRIC_RETREAT_RATE: float = 0.5  # stages/hour


def _seconds_to_drop(drop: float, rate_per_hour: float) -> float:
    """Seconds needed to decay a meter by *drop* at *rate_per_hour*."""
    return (drop / rate_per_hour) * _SECONDS_PER_HOUR


def _avatar(
    hunger: float = 1.0,
    hygiene: float = 1.0,
    social: float = 1.0,
    stage: VampiricStage = VampiricStage.NONE,
    needs_updated: float = 0.0,
    social_updated: float = 0.0,
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=needs_updated),
        social=SocialState(
            score=social, vampiric_stage=stage, last_interaction=social_updated
        ),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# GameEventKind
# ---------------------------------------------------------------------------


class TestGameEventKind:
    def test_all_kinds_defined(self) -> None:
        names = {k.name for k in GameEventKind}
        assert names == {
            "VAMPIRIC_ADVANCE",
            "VAMPIRIC_RETREAT",
            "HUNGER_WARNING",
            "HUNGER_CRITICAL",
            "HYGIENE_WARNING",
            "HYGIENE_CRITICAL",
            "SOCIAL_WARNING",
            "SOCIAL_CRITICAL",
            "LEVEL_UP_READY",
        }

    def test_values_are_strings(self) -> None:
        for kind in GameEventKind:
            assert isinstance(kind.value, str)


# ---------------------------------------------------------------------------
# GameEvent
# ---------------------------------------------------------------------------


class TestGameEvent:
    def test_is_frozen(self) -> None:
        event = GameEvent(kind=GameEventKind.HUNGER_WARNING, timestamp=100.0)
        assert dataclasses.is_dataclass(event)
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.timestamp = 0.0  # type: ignore[misc]

    def test_stores_kind_and_timestamp(self) -> None:
        event = GameEvent(kind=GameEventKind.VAMPIRIC_ADVANCE, timestamp=42.0)
        assert event.kind is GameEventKind.VAMPIRIC_ADVANCE
        assert event.timestamp == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# TickResult
# ---------------------------------------------------------------------------


class TestTickResult:
    def test_is_frozen(self) -> None:
        av = _avatar()
        result = TickResult(avatar=av, events=())
        assert dataclasses.is_dataclass(result)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.events = ()  # type: ignore[misc]

    def test_stores_avatar_and_events(self) -> None:
        av = _avatar()
        event = GameEvent(kind=GameEventKind.HUNGER_WARNING, timestamp=1.0)
        result = TickResult(avatar=av, events=(event,))
        assert result.avatar is av
        assert result.events == (event,)


# ---------------------------------------------------------------------------
# process_tick — decay correctness
# ---------------------------------------------------------------------------


class TestProcessTickDecay:
    def test_returns_tick_result(self) -> None:
        av = _avatar()
        result = process_tick(av, 0.0, PRODUCTION_PACE)
        assert isinstance(result, TickResult)

    def test_returns_new_avatar_object(self) -> None:
        av = _avatar()
        result = process_tick(av, 0.0, PRODUCTION_PACE)
        assert result.avatar is not av

    def test_zero_elapsed_no_hunger_change(self) -> None:
        av = _avatar(hunger=0.8, needs_updated=100.0, social_updated=100.0)
        result = process_tick(av, 100.0, PRODUCTION_PACE)
        assert result.avatar.needs.hunger == pytest.approx(0.8)

    def test_zero_elapsed_no_hygiene_change(self) -> None:
        av = _avatar(hygiene=0.7, needs_updated=100.0, social_updated=100.0)
        result = process_tick(av, 100.0, PRODUCTION_PACE)
        assert result.avatar.needs.hygiene == pytest.approx(0.7)

    def test_zero_elapsed_no_social_change(self) -> None:
        av = _avatar(social=0.6, needs_updated=100.0, social_updated=100.0)
        result = process_tick(av, 100.0, PRODUCTION_PACE)
        assert result.avatar.social.score == pytest.approx(0.6)

    def test_hunger_decreases_over_time(self) -> None:
        elapsed = _SECONDS_PER_HOUR  # 1 hour
        av = _avatar(hunger=1.0)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        assert result.avatar.needs.hunger == pytest.approx(1.0 - _HUNGER_RATE)

    def test_hygiene_decreases_over_time(self) -> None:
        elapsed = _SECONDS_PER_HOUR
        av = _avatar(hygiene=1.0)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        assert result.avatar.needs.hygiene == pytest.approx(1.0 - _HYGIENE_RATE)

    def test_social_score_decreases_over_time(self) -> None:
        elapsed = _SECONDS_PER_HOUR
        av = _avatar(social=1.0)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        assert result.avatar.social.score == pytest.approx(1.0 - _SOCIAL_RATE)

    def test_needs_last_updated_advanced_to_now(self) -> None:
        av = _avatar(needs_updated=0.0)
        now = 500.0
        result = process_tick(av, now, PRODUCTION_PACE)
        assert result.avatar.needs.last_updated == pytest.approx(now)

    def test_social_last_interaction_advanced_to_now(self) -> None:
        av = _avatar(social_updated=0.0)
        now = 500.0
        result = process_tick(av, now, PRODUCTION_PACE)
        assert result.avatar.social.last_interaction == pytest.approx(now)

    def test_level_unchanged(self) -> None:
        av = _avatar()
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        assert result.avatar.level == av.level

    def test_id_preserved(self) -> None:
        av = _avatar()
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        assert result.avatar.id == av.id

    def test_created_at_preserved(self) -> None:
        av = _avatar()
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        assert result.avatar.created_at == pytest.approx(av.created_at)

    def test_negative_needs_elapsed_clamped_no_decay(self) -> None:
        """now < needs.last_updated → elapsed clamped to zero → no decay."""
        av = _avatar(hunger=0.8, needs_updated=1000.0, social_updated=0.0)
        result = process_tick(av, 500.0, PRODUCTION_PACE)
        assert result.avatar.needs.hunger == pytest.approx(0.8)

    def test_negative_social_elapsed_clamped_no_decay(self) -> None:
        """now < social.last_interaction → elapsed clamped to zero → no decay."""
        av = _avatar(social=0.8, needs_updated=0.0, social_updated=1000.0)
        result = process_tick(av, 500.0, PRODUCTION_PACE)
        assert result.avatar.social.score == pytest.approx(0.8)

    def test_meters_clamped_at_zero(self) -> None:
        av = _avatar(hunger=0.01)
        result = process_tick(av, 8 * _SECONDS_PER_HOUR, PRODUCTION_PACE)
        assert result.avatar.needs.hunger == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# process_tick — separate elapsed times for needs vs social
# ---------------------------------------------------------------------------


class TestProcessTickSeparateElapsed:
    def test_needs_uses_needs_last_updated(self) -> None:
        """Needs decay elapsed = now - needs.last_updated."""
        needs_updated = 0.0
        social_updated = _SECONDS_PER_HOUR  # social updated 1 hour later
        now = 2 * _SECONDS_PER_HOUR  # 2h after needs, 1h after social

        av = _avatar(
            hunger=1.0,
            social=1.0,
            needs_updated=needs_updated,
            social_updated=social_updated,
        )
        result = process_tick(av, now, PRODUCTION_PACE)

        # Hunger: 2 hours of decay
        assert result.avatar.needs.hunger == pytest.approx(1.0 - _HUNGER_RATE * 2)

    def test_social_uses_social_last_interaction(self) -> None:
        """Social decay elapsed = now - social.last_interaction."""
        needs_updated = 0.0
        social_updated = _SECONDS_PER_HOUR
        now = 2 * _SECONDS_PER_HOUR

        av = _avatar(
            hunger=1.0,
            social=1.0,
            needs_updated=needs_updated,
            social_updated=social_updated,
        )
        result = process_tick(av, now, PRODUCTION_PACE)

        # Social: 1 hour of decay
        assert result.avatar.social.score == pytest.approx(1.0 - _SOCIAL_RATE)

    def test_needs_with_zero_elapsed_social_with_positive(self) -> None:
        """Social decays independently when needs.last_updated == now."""
        now = _SECONDS_PER_HOUR
        av = _avatar(hunger=0.8, social=1.0, needs_updated=now, social_updated=0.0)
        result = process_tick(av, now, PRODUCTION_PACE)

        assert result.avatar.needs.hunger == pytest.approx(0.8)  # no needs decay
        assert result.avatar.social.score == pytest.approx(1.0 - _SOCIAL_RATE)

    def test_social_with_zero_elapsed_needs_with_positive(self) -> None:
        """Needs decay independently when social.last_interaction == now."""
        now = _SECONDS_PER_HOUR
        av = _avatar(hunger=1.0, social=0.8, needs_updated=0.0, social_updated=now)
        result = process_tick(av, now, PRODUCTION_PACE)

        assert result.avatar.needs.hunger == pytest.approx(1.0 - _HUNGER_RATE)
        assert result.avatar.social.score == pytest.approx(0.8)  # no social decay


# ---------------------------------------------------------------------------
# process_tick — event detection
# ---------------------------------------------------------------------------


class TestProcessTickNoEvents:
    def test_no_events_when_no_thresholds_crossed(self) -> None:
        av = _avatar(hunger=1.0, hygiene=1.0, social=1.0)
        result = process_tick(av, 60.0, PRODUCTION_PACE)
        assert result.events == ()

    def test_no_events_when_already_below_threshold(self) -> None:
        """Pre-existing critical state does not re-emit event."""
        av = _avatar(hunger=0.10, hygiene=0.10, social=0.10)
        # Enough time to decay further, but thresholds already crossed
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING not in kinds
        assert GameEventKind.HUNGER_CRITICAL not in kinds
        assert GameEventKind.HYGIENE_WARNING not in kinds
        assert GameEventKind.HYGIENE_CRITICAL not in kinds
        assert GameEventKind.SOCIAL_WARNING not in kinds
        assert GameEventKind.SOCIAL_CRITICAL not in kinds


class TestProcessTickHungerEvents:
    def test_hunger_warning_emitted_on_crossing(self) -> None:
        above = _HUNGER_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HUNGER_RATE)
        av = _avatar(hunger=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING in kinds

    def test_hunger_warning_not_emitted_when_already_below(self) -> None:
        av = _avatar(hunger=_HUNGER_WARNING_THRESHOLD - 0.01)
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING not in kinds

    def test_hunger_critical_emitted_on_crossing(self) -> None:
        above = _HUNGER_CRITICAL_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HUNGER_RATE)
        av = _avatar(hunger=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_CRITICAL in kinds

    def test_hunger_critical_not_emitted_when_already_below(self) -> None:
        av = _avatar(hunger=_HUNGER_CRITICAL_THRESHOLD - 0.01)
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_CRITICAL not in kinds

    def test_both_hunger_events_on_large_drop(self) -> None:
        """Hunger crossing both thresholds in one tick emits both events."""
        start = _HUNGER_WARNING_THRESHOLD + 0.01
        # Drop past both thresholds
        elapsed = _seconds_to_drop(
            start - _HUNGER_CRITICAL_THRESHOLD + 0.02, _HUNGER_RATE
        )
        av = _avatar(hunger=start)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HUNGER_WARNING in kinds
        assert GameEventKind.HUNGER_CRITICAL in kinds


class TestProcessTickHygieneEvents:
    def test_hygiene_warning_emitted_on_crossing(self) -> None:
        above = _HYGIENE_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HYGIENE_RATE)
        av = _avatar(hygiene=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HYGIENE_WARNING in kinds

    def test_hygiene_warning_not_emitted_when_already_below(self) -> None:
        av = _avatar(hygiene=_HYGIENE_WARNING_THRESHOLD - 0.01)
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HYGIENE_WARNING not in kinds

    def test_hygiene_critical_emitted_on_crossing(self) -> None:
        above = _HYGIENE_CRITICAL_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HYGIENE_RATE)
        av = _avatar(hygiene=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HYGIENE_CRITICAL in kinds

    def test_both_hygiene_events_on_large_drop(self) -> None:
        start = _HYGIENE_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(
            start - _HYGIENE_CRITICAL_THRESHOLD + 0.02, _HYGIENE_RATE
        )
        av = _avatar(hygiene=start)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.HYGIENE_WARNING in kinds
        assert GameEventKind.HYGIENE_CRITICAL in kinds


class TestProcessTickSocialEvents:
    def test_social_warning_emitted_on_crossing(self) -> None:
        above = _SOCIAL_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _SOCIAL_RATE)
        av = _avatar(social=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.SOCIAL_WARNING in kinds

    def test_social_warning_not_emitted_when_already_below(self) -> None:
        av = _avatar(social=_SOCIAL_WARNING_THRESHOLD - 0.01)
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.SOCIAL_WARNING not in kinds

    def test_social_critical_emitted_on_crossing(self) -> None:
        above = _SOCIAL_CRITICAL_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _SOCIAL_RATE)
        av = _avatar(social=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.SOCIAL_CRITICAL in kinds

    def test_both_social_events_on_large_drop(self) -> None:
        start = _SOCIAL_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(
            start - _SOCIAL_CRITICAL_THRESHOLD + 0.02, _SOCIAL_RATE
        )
        av = _avatar(social=start)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.SOCIAL_WARNING in kinds
        assert GameEventKind.SOCIAL_CRITICAL in kinds


class TestProcessTickVampiricEvents:
    def test_vampiric_advance_emitted_when_stage_worsens(self) -> None:
        """After 12 h at score=0 the stage advances from NONE to PALLOR."""
        av = _avatar(social=0.0, stage=VampiricStage.NONE)
        elapsed = _VAMPIRIC_ADVANCE_HOURS * _SECONDS_PER_HOUR + 1.0
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.VAMPIRIC_ADVANCE in kinds
        assert result.avatar.social.vampiric_stage is VampiricStage.PALLOR

    def test_vampiric_retreat_emitted_when_stage_improves(self) -> None:
        """After 2 h with score > 0, stage retreats from PALLOR to NONE."""
        av = _avatar(social=0.5, stage=VampiricStage.PALLOR)
        # 2 hours → stages_retreated = int(2 * 0.5) = 1 → PALLOR → NONE
        elapsed = 2.0 * _SECONDS_PER_HOUR
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.VAMPIRIC_RETREAT in kinds
        assert result.avatar.social.vampiric_stage is VampiricStage.NONE

    def test_no_vampiric_event_when_stage_unchanged(self) -> None:
        av = _avatar(social=1.0, stage=VampiricStage.NONE)
        result = process_tick(av, _SECONDS_PER_HOUR, PRODUCTION_PACE)
        kinds = {e.kind for e in result.events}
        assert GameEventKind.VAMPIRIC_ADVANCE not in kinds
        assert GameEventKind.VAMPIRIC_RETREAT not in kinds


class TestProcessTickEventTimestamp:
    def test_events_carry_now_timestamp(self) -> None:
        above = _HUNGER_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(0.02, _HUNGER_RATE)
        av = _avatar(hunger=above)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        for event in result.events:
            assert event.timestamp == pytest.approx(elapsed)

    def test_multiple_events_all_carry_same_timestamp(self) -> None:
        start = _HUNGER_WARNING_THRESHOLD + 0.01
        elapsed = _seconds_to_drop(
            start - _HUNGER_CRITICAL_THRESHOLD + 0.02, _HUNGER_RATE
        )
        av = _avatar(hunger=start)
        result = process_tick(av, elapsed, PRODUCTION_PACE)
        assert len(result.events) >= 2
        timestamps = {e.timestamp for e in result.events}
        assert len(timestamps) == 1
