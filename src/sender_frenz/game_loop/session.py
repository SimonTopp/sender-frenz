"""Player-session model for the game loop.

:func:`open_session` is the entry point called when a player opens the
app.  It applies pending decay, computes full status summaries, checks
level-up eligibility, collects warning and login quips, and returns a
single :class:`SessionState` bundle containing everything the display
layer needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sender_frenz.character_builder.appearance import compute_appearance
from sender_frenz.common.levels import LevelConfig, is_level_up_available
from sender_frenz.common.quips import QuipTrigger
from sender_frenz.game_loop.tick import (
    GameEvent,
    GameEventKind,
    TickResult,
    process_tick,
)
from sender_frenz.required_maintenance.needs import NeedsSummary, needs_summary
from sender_frenz.social_maintenance.effects import SocialSummary, social_summary

if TYPE_CHECKING:
    from sender_frenz.character_builder.appearance import AppearanceState
    from sender_frenz.common.config import GamePace
    from sender_frenz.common.models import Avatar
    from sender_frenz.common.quips import QuipCaller
    from sender_frenz.common.types import Timestamp
    from sender_frenz.social_maintenance.history import InteractionHistory

# ---------------------------------------------------------------------------
# Quip trigger mapping
# ---------------------------------------------------------------------------

_EVENT_QUIP_TRIGGERS: dict[GameEventKind, QuipTrigger] = {
    GameEventKind.HUNGER_WARNING: QuipTrigger.HUNGER_WARNING,
    GameEventKind.HUNGER_CRITICAL: QuipTrigger.HUNGER_CRITICAL,
    GameEventKind.HYGIENE_WARNING: QuipTrigger.HYGIENE_WARNING,
    GameEventKind.HYGIENE_CRITICAL: QuipTrigger.HYGIENE_CRITICAL,
    GameEventKind.SOCIAL_WARNING: QuipTrigger.SOCIAL_WARNING,
    GameEventKind.SOCIAL_CRITICAL: QuipTrigger.SOCIAL_CRITICAL,
}

# ---------------------------------------------------------------------------
# SessionState
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionState:
    """Full display-layer payload for a player session.

    Contains everything the client needs to render current state, trigger
    animations, and present quips — without requiring additional queries
    to the game engine.

    Attributes:
        avatar: Updated avatar state after applying pending decay.
        needs_summary: Physical need status snapshot.
        social_summary: Social health status snapshot.
        appearance: Visual appearance state derived from current stats.
        level_up_available: Whether the avatar qualifies for a level-up.
        events: State-change events that occurred; the display layer uses
            these to trigger animations.  Includes
            :attr:`~GameEventKind.LEVEL_UP_READY` when a level-up first
            becomes available.
        quips: Quips to present; the ``LOGIN`` quip is always first,
            followed by one quip per threshold-warning event.
    """

    avatar: Avatar
    needs_summary: NeedsSummary
    social_summary: SocialSummary
    appearance: AppearanceState
    level_up_available: bool
    events: tuple[GameEvent, ...]
    quips: tuple[str, ...]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def open_session(
    avatar: Avatar,
    history: InteractionHistory,
    sustained_since: Timestamp | None,
    now: Timestamp,
    pace: GamePace,
    quip_caller: QuipCaller,
) -> SessionState:
    """Apply pending decay and build the full session state bundle.

    Called when a player opens the app.  Applies all time-based decay
    since the avatar was last updated, computes status summaries, checks
    level-up eligibility, and collects the login and any warning quips.

    Args:
        avatar: Last-known avatar state.
        history: Interaction history.  Reserved for Phase 7 usage;
            accepted here for API stability.
        sustained_since: Timestamp at which the avatar first crossed the
            combined-health threshold in the current streak, or ``None``
            if the threshold has not been sustained.  Tracked by the
            persistence layer.
        now: Current Unix epoch timestamp.
        pace: Game pace multiplier used to derive decay rates.
        quip_caller: Injectable quip delivery function.

    Returns:
        A :class:`SessionState` with the updated avatar, status summaries,
        appearance state, level-up flag, event log, and quips.
    """
    tick: TickResult = process_tick(avatar, now, pace)

    n_summary: NeedsSummary = needs_summary(tick.avatar)
    s_summary: SocialSummary = social_summary(tick.avatar)
    appearance: AppearanceState = compute_appearance(tick.avatar)

    level_up: bool = False
    if sustained_since is not None:
        level_config = LevelConfig.from_pace(pace)
        level_up = is_level_up_available(
            tick.avatar, sustained_since, now, level_config
        )

    # Build event list; append LEVEL_UP_READY when newly eligible
    events: list[GameEvent] = list(tick.events)
    if level_up:
        events.append(GameEvent(kind=GameEventKind.LEVEL_UP_READY, timestamp=now))

    # LOGIN quip always first; one quip per threshold-crossing event
    quips: list[str] = [quip_caller(QuipTrigger.LOGIN)]
    for event in events:
        trigger = _EVENT_QUIP_TRIGGERS.get(event.kind)
        if trigger is not None:
            quips.append(quip_caller(trigger))

    del history  # reserved for Phase 7; suppresses unused-argument lint

    return SessionState(
        avatar=tick.avatar,
        needs_summary=n_summary,
        social_summary=s_summary,
        appearance=appearance,
        level_up_available=level_up,
        events=tuple(events),
        quips=tuple(quips),
    )
