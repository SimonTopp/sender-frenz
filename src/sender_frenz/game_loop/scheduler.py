"""Background tick scheduler.

Periodically applies game-loop decay to every stored avatar and publishes
any resulting :class:`~sender_frenz.game_loop.tick.GameEvent` instances to
the :class:`~sender_frenz.api.events.EventBus`.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace
from typing import TYPE_CHECKING

from sender_frenz.game_loop.tick import process_tick

if TYPE_CHECKING:
    from sender_frenz.api.events import EventBus
    from sender_frenz.common.config import GamePace
    from sender_frenz.persistence.store import StoreProtocol

_DEFAULT_INTERVAL: float = 30.0


def _tick_all(store: StoreProtocol, bus: EventBus, pace: GamePace) -> None:
    """Apply one tick of decay to every avatar in *store*.

    Loads each snapshot, runs :func:`~sender_frenz.game_loop.tick.process_tick`,
    saves the updated snapshot, and publishes any events to *bus*.
    """
    now = time.time()
    for avatar_id in store.list_ids():
        snapshot = store.load(avatar_id)
        assert snapshot is not None
        result = process_tick(snapshot.avatar, now, pace)
        store.save(replace(snapshot, avatar=result.avatar, last_tick=now))
        if result.events:
            bus.publish(avatar_id, result.events)


async def run_scheduler(
    store: StoreProtocol,
    bus: EventBus,
    pace: GamePace,
    interval: float = _DEFAULT_INTERVAL,
) -> None:
    """Run the background tick loop until cancelled.

    Sleeps for *interval* seconds, then calls :func:`_tick_all`.  Designed
    to be run as an :mod:`asyncio` task; cancellation exits the loop cleanly.

    Args:
        store: Snapshot store to load from and save to.
        bus: Event bus to publish game events on.
        pace: Game pace multiplier forwarded to :func:`process_tick`.
        interval: Seconds between ticks.  Defaults to 30.
    """
    while True:
        await asyncio.sleep(interval)
        _tick_all(store, bus, pace)
