"""Action endpoint: POST /action/{kind}.

Dispatches feed, clean, visit, gift, and chat actions to the appropriate
game-engine function, updates the snapshot, and returns the updated avatar
state with a THE SYSTEM quip.

Note: top-level type imports are required so FastAPI's ``get_type_hints()``
can resolve ``Annotated[T, Depends(f)]`` parameter annotations at runtime.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from sender_frenz.api._helpers import make_snapshot, update_sustained_since
from sender_frenz.api.deps import (
    get_avatar_id,
    get_now,
    get_pace,
    get_quip_caller,
    get_store,
)
from sender_frenz.api.models import (
    ActionKind,
    ActionResponse,
    NeedsResponse,
    SocialResponse,
)
from sender_frenz.common.config import GamePace
from sender_frenz.common.models import Avatar
from sender_frenz.common.quips import QuipCaller
from sender_frenz.common.types import AvatarId, Timestamp
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.persistence.store import StoreProtocol
from sender_frenz.required_maintenance.actions import clean, feed
from sender_frenz.social_maintenance.history import add_event
from sender_frenz.social_maintenance.interactions import InteractionKind, interact

router = APIRouter()

# Map social action kinds to InteractionKind values.
_SOCIAL_KINDS: dict[ActionKind, InteractionKind] = {
    ActionKind.VISIT: InteractionKind.VISIT,
    ActionKind.GIFT: InteractionKind.GIFT,
    ActionKind.CHAT: InteractionKind.CHAT,
}


def _dispatch(
    kind: ActionKind,
    snapshot: GameSnapshot,
    now: Timestamp,
    quip_caller: QuipCaller,
) -> tuple[Avatar, str, GameSnapshot]:
    """Dispatch *kind* to the appropriate game-engine function.

    Args:
        kind: The action to perform.
        snapshot: Current snapshot (used for avatar and history).
        now: Current timestamp.
        quip_caller: Quip delivery callable.

    Returns:
        A ``(new_avatar, quip, base_snapshot)`` triple.  For social
        interactions the returned snapshot has its history updated;
        for maintenance actions the original snapshot is returned unchanged.
    """
    avatar = snapshot.avatar
    history = snapshot.history

    if kind == ActionKind.FEED:
        result = feed(avatar, now, quip_caller)
        return result.avatar, result.quip, snapshot

    if kind == ActionKind.CLEAN:
        result = clean(avatar, now, quip_caller)
        return result.avatar, result.quip, snapshot

    interaction_kind = _SOCIAL_KINDS[kind]
    i_result = interact(avatar, interaction_kind, now, quip_caller)
    new_history = add_event(history, interaction_kind, now)
    base = GameSnapshot(
        avatar=i_result.avatar,
        room=snapshot.room,
        history=new_history,
        sustained_since=snapshot.sustained_since,
        last_tick=snapshot.last_tick,
    )
    return i_result.avatar, i_result.quip, base


@router.post("/action/{kind}")
async def perform_action(
    kind: ActionKind,
    avatar_id: Annotated[AvatarId, Depends(get_avatar_id)],
    store: Annotated[StoreProtocol, Depends(get_store)],
    pace: Annotated[GamePace, Depends(get_pace)],
    now: Annotated[Timestamp, Depends(get_now)],
    quip_caller: Annotated[QuipCaller, Depends(get_quip_caller)],
) -> ActionResponse:
    """Perform a single player action and return the updated avatar state.

    Loads the snapshot for the requesting avatar (bootstrapping if absent),
    dispatches the action, recomputes ``sustained_since``, saves, and
    returns the action result.

    Args:
        kind: Action to perform; validated against
            :class:`~sender_frenz.api.models.ActionKind`.
        avatar_id: Parsed from the ``Avatar-Id`` request header.
        store: Snapshot store dependency.
        pace: Game pace dependency.
        now: Current timestamp dependency.
        quip_caller: Quip caller dependency.

    Returns:
        An :class:`~sender_frenz.api.models.ActionResponse` with updated
        meters and quip.
    """
    snapshot = store.load(avatar_id) or make_snapshot(avatar_id, now)
    new_avatar, quip, base_snapshot = _dispatch(kind, snapshot, now, quip_caller)

    new_sustained = update_sustained_since(
        new_avatar, base_snapshot.sustained_since, now, pace
    )
    updated = GameSnapshot(
        avatar=new_avatar,
        room=base_snapshot.room,
        history=base_snapshot.history,
        sustained_since=new_sustained,
        last_tick=base_snapshot.last_tick,
    )
    store.save(updated)

    return ActionResponse(
        avatar_id=str(avatar_id),
        needs=NeedsResponse(
            hunger=new_avatar.needs.hunger,
            hygiene=new_avatar.needs.hygiene,
        ),
        social=SocialResponse(
            score=new_avatar.social.score,
            vampiric_stage=new_avatar.social.vampiric_stage.name.lower(),
        ),
        quip=quip,
    )
