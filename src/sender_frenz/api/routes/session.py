"""Session and avatar read endpoints.

``POST /session/open`` — apply pending decay and return the full session bundle.
``GET /avatar/{avatar_id}`` — return the current snapshot without advancing time.

Note: top-level type imports are required so FastAPI's ``get_type_hints()``
can resolve ``Annotated[T, Depends(f)]`` parameter annotations at runtime.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sender_frenz.api._helpers import make_snapshot, update_sustained_since
from sender_frenz.api.deps import (
    get_avatar_id,
    get_bus,
    get_now,
    get_pace,
    get_quip_caller,
    get_store,
)
from sender_frenz.api.events import EventBus
from sender_frenz.api.models import (
    AppearanceResponse,
    AvatarResponse,
    GameEventResponse,
    LevelResponse,
    NeedsResponse,
    NeedsSummaryResponse,
    SessionResponse,
    SocialResponse,
    SocialSummaryResponse,
)
from sender_frenz.character_builder.appearance import compute_appearance
from sender_frenz.common.config import GamePace
from sender_frenz.common.levels import LevelConfig, is_level_up_available
from sender_frenz.common.quips import QuipCaller
from sender_frenz.common.types import AvatarId, Timestamp
from sender_frenz.game_loop.session import open_session
from sender_frenz.game_loop.tick import GameEventKind
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.persistence.store import StoreProtocol

router = APIRouter()


def _build_session_response(
    snapshot: GameSnapshot,
    avatar_id: AvatarId,
    pace: GamePace,
    now: Timestamp,
    quip_caller: QuipCaller,
) -> tuple[SessionResponse, GameSnapshot]:
    """Run open_session and build both the HTTP response and the updated snapshot.

    Args:
        snapshot: Current snapshot loaded from the store (or freshly bootstrapped).
        avatar_id: The avatar's ID (used in the response body).
        pace: Game pace for decay calculations.
        now: Current timestamp.
        quip_caller: Quip delivery callable.

    Returns:
        A ``(SessionResponse, updated_GameSnapshot)`` tuple.
    """
    session = open_session(
        avatar=snapshot.avatar,
        history=snapshot.history,
        sustained_since=snapshot.sustained_since,
        now=now,
        pace=pace,
        quip_caller=quip_caller,
    )

    new_sustained = update_sustained_since(
        session.avatar, snapshot.sustained_since, now, pace
    )

    level_config = LevelConfig.from_pace(pace)
    level_up_available = new_sustained is not None and is_level_up_available(
        session.avatar, new_sustained, now, level_config
    )

    updated_snapshot = GameSnapshot(
        avatar=session.avatar,
        room=snapshot.room,
        history=snapshot.history,
        sustained_since=new_sustained,
        last_tick=now,
    )

    appearance = compute_appearance(session.avatar)
    av = session.avatar

    response = SessionResponse(
        avatar_id=str(avatar_id),
        needs=NeedsResponse(hunger=av.needs.hunger, hygiene=av.needs.hygiene),
        social=SocialResponse(
            score=av.social.score,
            vampiric_stage=av.social.vampiric_stage.name.lower(),
        ),
        level=LevelResponse(
            current=av.level.current,
            skin_upgrades=list(av.level.skin_upgrades),
            room_upgrades=list(av.level.room_upgrades),
        ),
        needs_summary=NeedsSummaryResponse(
            hunger=session.needs_summary.hunger,
            hygiene=session.needs_summary.hygiene,
            hungry=session.needs_summary.hungry,
            dirty=session.needs_summary.dirty,
            over_nourished=session.needs_summary.over_nourished,
            over_scrubbed=session.needs_summary.over_scrubbed,
        ),
        social_summary=SocialSummaryResponse(
            score=session.social_summary.score,
            vampiric_stage=session.social_summary.vampiric_stage.name.lower(),
            is_isolated=session.social_summary.is_isolated,
            is_thriving=session.social_summary.is_thriving,
            stage_label=session.social_summary.stage_label,
        ),
        appearance=AppearanceResponse(
            vampiric_stage=appearance.vampiric_stage.name.lower(),
            hunger_visual=appearance.hunger_visual,
            hygiene_visual=appearance.hygiene_visual,
            skin_slug=appearance.skin_slug,
            composite_label=appearance.composite_label,
        ),
        level_up_available=level_up_available,
        events=[
            GameEventResponse(kind=e.kind.value, timestamp=e.timestamp)
            for e in session.events
            if e.kind != GameEventKind.LEVEL_UP_READY
        ],
        quips=list(session.quips),
    )
    return response, updated_snapshot


@router.post("/session/open")
async def open_session_endpoint(
    avatar_id: Annotated[AvatarId, Depends(get_avatar_id)],
    store: Annotated[StoreProtocol, Depends(get_store)],
    bus: Annotated[EventBus, Depends(get_bus)],
    pace: Annotated[GamePace, Depends(get_pace)],
    now: Annotated[Timestamp, Depends(get_now)],
    quip_caller: Annotated[QuipCaller, Depends(get_quip_caller)],
) -> SessionResponse:
    """Apply pending decay and return the full session state bundle.

    Loads the snapshot for the requesting avatar (creating a fresh one if none
    exists), applies time-based decay via
    :func:`~sender_frenz.game_loop.session.open_session`, updates
    ``sustained_since``, saves the result, and publishes tick events to the
    SSE bus.

    Args:
        avatar_id: Parsed from the ``Avatar-Id`` request header.
        store: Snapshot store dependency.
        bus: Event bus dependency.
        pace: Game pace dependency.
        now: Current timestamp dependency.
        quip_caller: Quip caller dependency.

    Returns:
        A :class:`~sender_frenz.api.models.SessionResponse` with the updated
        avatar state, status summaries, appearance, level-up flag, events, and quips.
    """
    snapshot = store.load(avatar_id) or make_snapshot(avatar_id, now)
    response, updated = _build_session_response(
        snapshot, avatar_id, pace, now, quip_caller
    )
    store.save(updated)
    bus.publish(avatar_id, [])
    return response


@router.get("/avatar/{avatar_id}")
async def get_avatar_endpoint(
    avatar_id: UUID,
    store: Annotated[StoreProtocol, Depends(get_store)],
) -> AvatarResponse:
    """Return the current snapshot without advancing time.

    Args:
        avatar_id: Avatar UUID parsed from the path.
        store: Snapshot store dependency.

    Returns:
        An :class:`~sender_frenz.api.models.AvatarResponse` with the stored state.

    Raises:
        :class:`~fastapi.HTTPException` (404): If no snapshot exists for
            *avatar_id*.
    """
    aid = AvatarId(avatar_id)
    snapshot = store.load(aid)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Avatar not found")
    av = snapshot.avatar
    return AvatarResponse(
        avatar_id=str(aid),
        needs=NeedsResponse(hunger=av.needs.hunger, hygiene=av.needs.hygiene),
        social=SocialResponse(
            score=av.social.score,
            vampiric_stage=av.social.vampiric_stage.name.lower(),
        ),
        level=LevelResponse(
            current=av.level.current,
            skin_upgrades=list(av.level.skin_upgrades),
            room_upgrades=list(av.level.room_upgrades),
        ),
        sustained_since=snapshot.sustained_since,
        last_tick=snapshot.last_tick,
    )
