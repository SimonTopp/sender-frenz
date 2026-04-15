"""Tests for sender_frenz.api.events.EventBus."""

import asyncio
from uuid import UUID

from sender_frenz.api.events import EventBus
from sender_frenz.common.types import AvatarId
from sender_frenz.game_loop.tick import GameEvent, GameEventKind

ID_A = AvatarId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
ID_B = AvatarId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
NOW = 1_000_000.0


def _event(kind: GameEventKind = GameEventKind.HUNGER_WARNING) -> GameEvent:
    return GameEvent(kind=kind, timestamp=NOW)


# ---------------------------------------------------------------------------
# subscribe
# ---------------------------------------------------------------------------


def test_subscribe_returns_queue():
    bus = EventBus()
    q = bus.subscribe(ID_A)
    assert isinstance(q, asyncio.Queue)


def test_subscribe_twice_returns_two_queues():
    bus = EventBus()
    q1 = bus.subscribe(ID_A)
    q2 = bus.subscribe(ID_A)
    assert q1 is not q2


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------


def test_publish_delivers_to_subscriber():
    bus = EventBus()
    q = bus.subscribe(ID_A)
    event = _event()
    bus.publish(ID_A, [event])
    assert q.qsize() == 1
    assert q.get_nowait() == event


def test_publish_delivers_to_all_subscribers():
    bus = EventBus()
    q1 = bus.subscribe(ID_A)
    q2 = bus.subscribe(ID_A)
    event = _event()
    bus.publish(ID_A, [event])
    assert q1.get_nowait() == event
    assert q2.get_nowait() == event


def test_publish_does_not_deliver_to_other_avatar():
    bus = EventBus()
    qa = bus.subscribe(ID_A)
    qb = bus.subscribe(ID_B)
    bus.publish(ID_A, [_event()])
    assert qa.qsize() == 1
    assert qb.qsize() == 0


def test_publish_multiple_events_preserves_order():
    bus = EventBus()
    q = bus.subscribe(ID_A)
    events = [
        GameEvent(kind=GameEventKind.HUNGER_WARNING, timestamp=NOW),
        GameEvent(kind=GameEventKind.HYGIENE_CRITICAL, timestamp=NOW + 1),
    ]
    bus.publish(ID_A, events)
    assert q.get_nowait() == events[0]
    assert q.get_nowait() == events[1]


def test_publish_no_subscribers_is_no_op():
    bus = EventBus()
    bus.publish(ID_A, [_event()])  # should not raise


# ---------------------------------------------------------------------------
# unsubscribe
# ---------------------------------------------------------------------------


def test_unsubscribe_removes_queue():
    bus = EventBus()
    q = bus.subscribe(ID_A)
    bus.unsubscribe(ID_A, q)
    bus.publish(ID_A, [_event()])
    assert q.qsize() == 0


def test_unsubscribe_removes_only_specified_queue():
    bus = EventBus()
    q1 = bus.subscribe(ID_A)
    q2 = bus.subscribe(ID_A)
    bus.unsubscribe(ID_A, q1)
    bus.publish(ID_A, [_event()])
    assert q1.qsize() == 0
    assert q2.qsize() == 1


def test_unsubscribe_cleans_up_empty_avatar_entry():
    bus = EventBus()
    q = bus.subscribe(ID_A)
    bus.unsubscribe(ID_A, q)
    assert ID_A not in bus._queues


def test_unsubscribe_unknown_avatar_is_no_op():
    bus = EventBus()
    q: asyncio.Queue[GameEvent | None] = asyncio.Queue()
    bus.unsubscribe(ID_A, q)  # should not raise


def test_unsubscribe_queue_not_in_list_is_no_op():
    bus = EventBus()
    bus.subscribe(ID_A)
    other_q: asyncio.Queue[GameEvent | None] = asyncio.Queue()
    bus.unsubscribe(ID_A, other_q)  # should not raise
