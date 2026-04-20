"""Tests for sender_frenz.game_loop.scheduler."""

from __future__ import annotations

import asyncio
import time
from contextlib import suppress
from dataclasses import replace
from uuid import uuid4

import pytest

from sender_frenz.api.events import EventBus
from sender_frenz.common.config import FAST_TEST_PACE
from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    Room,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId, RoomId
from sender_frenz.game_loop.scheduler import _tick_all, run_scheduler
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.persistence.store import MemoryStore
from sender_frenz.social_maintenance.history import create_history

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _avatar(
    hunger: float = 1.0, hygiene: float = 1.0, last_updated: float = 0.0
) -> Avatar:
    return Avatar(
        id=AvatarId(uuid4()),
        needs=NeedState(hunger=hunger, hygiene=hygiene, last_updated=last_updated),
        social=SocialState(
            score=1.0, vampiric_stage=VampiricStage.NONE, last_interaction=0.0
        ),
        level=Level(current=0, skin_upgrades=(), room_upgrades=()),
        created_at=0.0,
    )


def _snapshot(avatar: Avatar | None = None) -> GameSnapshot:
    if avatar is None:
        avatar = _avatar()
    return GameSnapshot(
        avatar=avatar,
        room=Room(
            id=RoomId(uuid4()), avatar_id=avatar.id, level=0, applied_upgrades=()
        ),
        history=create_history(),
        sustained_since=None,
        last_tick=0.0,
    )


# ---------------------------------------------------------------------------
# _tick_all
# ---------------------------------------------------------------------------


class TestTickAll:
    def test_empty_store_is_noop(self) -> None:
        _tick_all(MemoryStore(), EventBus(), FAST_TEST_PACE)

    def test_updates_snapshot_last_tick(self) -> None:
        store = MemoryStore()
        snap = _snapshot()
        store.save(snap)
        _tick_all(store, EventBus(), FAST_TEST_PACE)
        updated = store.load(snap.avatar.id)
        assert updated is not None
        assert updated.last_tick > snap.last_tick

    def test_publishes_events_on_threshold_crossing(self) -> None:
        store = MemoryStore()
        bus = EventBus()
        # last_updated far in the past → enormous elapsed → hunger drops to 0
        av = _avatar(hunger=0.51, last_updated=-1_000_000.0)
        snap = _snapshot(av)
        store.save(snap)
        queue = bus.subscribe(av.id)
        _tick_all(store, bus, FAST_TEST_PACE)
        assert not queue.empty()

    def test_raises_when_listed_id_has_no_snapshot(self) -> None:
        class BrokenStore:
            def load(self, avatar_id: AvatarId) -> GameSnapshot | None:
                return None

            def save(self, snapshot: GameSnapshot) -> None:
                pass

            def list_ids(self) -> tuple[AvatarId, ...]:
                return (AvatarId(uuid4()),)

        with pytest.raises(RuntimeError, match="listed but not found"):
            _tick_all(BrokenStore(), EventBus(), FAST_TEST_PACE)

    def test_no_events_when_no_threshold_crossed(self) -> None:
        store = MemoryStore()
        bus = EventBus()
        # last_updated=now → zero elapsed → no decay → no events
        av = _avatar(hunger=1.0, last_updated=time.time())
        av = replace(av, social=replace(av.social, last_interaction=time.time()))
        snap = _snapshot(av)
        store.save(snap)
        queue = bus.subscribe(av.id)
        _tick_all(store, bus, FAST_TEST_PACE)
        assert queue.empty()


# ---------------------------------------------------------------------------
# run_scheduler
# ---------------------------------------------------------------------------


class TestRunScheduler:
    async def test_cancels_cleanly(self) -> None:
        task = asyncio.create_task(
            run_scheduler(MemoryStore(), EventBus(), FAST_TEST_PACE, interval=1000.0)
        )
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        assert task.done()

    async def test_ticks_avatars_after_interval(self) -> None:
        store = MemoryStore()
        snap = _snapshot()
        store.save(snap)
        task = asyncio.create_task(
            run_scheduler(store, EventBus(), FAST_TEST_PACE, interval=0.01)
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        updated = store.load(snap.avatar.id)
        assert updated is not None
        assert updated.last_tick > snap.last_tick
