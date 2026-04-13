"""Tests for sender_frenz.social_maintenance.history."""

import dataclasses

import pytest

from sender_frenz.social_maintenance.history import (
    InteractionEvent,
    InteractionHistory,
    add_event,
    create_history,
    interactions_in_window,
    recent_events,
)
from sender_frenz.social_maintenance.interactions import InteractionKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VISIT = InteractionKind.VISIT
_GIFT = InteractionKind.GIFT
_CHAT = InteractionKind.CHAT


# ---------------------------------------------------------------------------
# InteractionEvent
# ---------------------------------------------------------------------------


class TestInteractionEvent:
    def test_is_frozen(self) -> None:
        event = InteractionEvent(kind=_VISIT, timestamp=100.0)
        assert dataclasses.is_dataclass(event)
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.timestamp = 0.0  # type: ignore[misc]

    def test_stores_kind_and_timestamp(self) -> None:
        event = InteractionEvent(kind=_GIFT, timestamp=42.0)
        assert event.kind is _GIFT
        assert event.timestamp == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# create_history
# ---------------------------------------------------------------------------


class TestCreateHistory:
    def test_returns_interaction_history(self) -> None:
        history = create_history()
        assert isinstance(history, InteractionHistory)

    def test_events_is_empty_tuple(self) -> None:
        history = create_history()
        assert history.events == ()

    def test_is_frozen(self) -> None:
        history = create_history()
        with pytest.raises(dataclasses.FrozenInstanceError):
            history.events = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# add_event
# ---------------------------------------------------------------------------


class TestAddEvent:
    def test_returns_new_history(self) -> None:
        h = create_history()
        h2 = add_event(h, _VISIT, 100.0)
        assert isinstance(h2, InteractionHistory)
        assert h2 is not h

    def test_original_history_unchanged(self) -> None:
        h = create_history()
        add_event(h, _VISIT, 100.0)
        assert h.events == ()

    def test_single_add_creates_one_event(self) -> None:
        h = add_event(create_history(), _VISIT, 100.0)
        assert len(h.events) == 1
        assert h.events[0].kind is _VISIT
        assert h.events[0].timestamp == pytest.approx(100.0)

    def test_events_stored_newest_first(self) -> None:
        h = create_history()
        h = add_event(h, _CHAT, 100.0)
        h = add_event(h, _GIFT, 200.0)
        h = add_event(h, _VISIT, 300.0)
        assert h.events[0].timestamp == pytest.approx(300.0)
        assert h.events[1].timestamp == pytest.approx(200.0)
        assert h.events[2].timestamp == pytest.approx(100.0)

    def test_kinds_preserved_in_order(self) -> None:
        h = create_history()
        h = add_event(h, _CHAT, 1.0)
        h = add_event(h, _GIFT, 2.0)
        h = add_event(h, _VISIT, 3.0)
        assert h.events[0].kind is _VISIT
        assert h.events[1].kind is _GIFT
        assert h.events[2].kind is _CHAT

    def test_multiple_adds_accumulate(self) -> None:
        h = create_history()
        for i in range(5):
            h = add_event(h, _CHAT, float(i))
        assert len(h.events) == 5


# ---------------------------------------------------------------------------
# recent_events
# ---------------------------------------------------------------------------


class TestRecentEvents:
    def test_empty_history_returns_empty(self) -> None:
        h = create_history()
        assert recent_events(h, since=0.0) == ()

    def test_all_events_after_since(self) -> None:
        h = create_history()
        h = add_event(h, _VISIT, 100.0)
        h = add_event(h, _GIFT, 200.0)
        result = recent_events(h, since=50.0)
        assert len(result) == 2

    def test_excludes_events_at_or_before_since(self) -> None:
        h = create_history()
        h = add_event(h, _VISIT, 100.0)
        h = add_event(h, _GIFT, 200.0)
        result = recent_events(h, since=100.0)
        # timestamp == since is excluded (strictly after)
        assert len(result) == 1
        assert result[0].timestamp == pytest.approx(200.0)

    def test_excludes_all_old_events(self) -> None:
        h = create_history()
        h = add_event(h, _VISIT, 50.0)
        h = add_event(h, _GIFT, 80.0)
        result = recent_events(h, since=200.0)
        assert result == ()

    def test_returns_newest_first(self) -> None:
        h = create_history()
        h = add_event(h, _CHAT, 100.0)
        h = add_event(h, _VISIT, 200.0)
        result = recent_events(h, since=0.0)
        assert result[0].timestamp == pytest.approx(200.0)
        assert result[1].timestamp == pytest.approx(100.0)

    def test_returns_tuple(self) -> None:
        h = add_event(create_history(), _VISIT, 100.0)
        assert isinstance(recent_events(h, since=0.0), tuple)

    def test_mixed_old_and_new(self) -> None:
        h = create_history()
        h = add_event(h, _CHAT, 10.0)
        h = add_event(h, _GIFT, 50.0)
        h = add_event(h, _VISIT, 150.0)
        h = add_event(h, _CHAT, 250.0)
        result = recent_events(h, since=100.0)
        assert len(result) == 2
        assert all(e.timestamp > 100.0 for e in result)


# ---------------------------------------------------------------------------
# interactions_in_window
# ---------------------------------------------------------------------------


class TestInteractionsInWindow:
    def test_empty_history_returns_zero(self) -> None:
        assert interactions_in_window(create_history(), since=0.0) == 0

    def test_all_events_in_window(self) -> None:
        h = create_history()
        h = add_event(h, _VISIT, 100.0)
        h = add_event(h, _GIFT, 200.0)
        assert interactions_in_window(h, since=0.0) == 2

    def test_no_events_in_window(self) -> None:
        h = create_history()
        h = add_event(h, _VISIT, 100.0)
        assert interactions_in_window(h, since=200.0) == 0

    def test_boundary_excluded(self) -> None:
        h = add_event(create_history(), _VISIT, 100.0)
        assert interactions_in_window(h, since=100.0) == 0

    def test_partial_window(self) -> None:
        h = create_history()
        h = add_event(h, _CHAT, 50.0)
        h = add_event(h, _GIFT, 150.0)
        h = add_event(h, _VISIT, 250.0)
        assert interactions_in_window(h, since=100.0) == 2

    def test_single_event_in_window(self) -> None:
        h = add_event(create_history(), _VISIT, 500.0)
        assert interactions_in_window(h, since=0.0) == 1
