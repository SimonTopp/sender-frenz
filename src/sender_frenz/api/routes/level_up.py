"""Level-up endpoint: POST /level-up.

Validates level-up eligibility, applies the chosen skin and room upgrade,
resets ``sustained_since``, saves the snapshot, and returns the new level
state with available follow-on options.

Note: top-level type imports are required so FastAPI's ``get_type_hints()``
can resolve ``Annotated[T, Depends(f)]`` parameter annotations at runtime.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from sender_frenz.api._helpers import make_snapshot
from sender_frenz.api.deps import (
    get_avatar_id,
    get_now,
    get_pace,
    get_store,
)
from sender_frenz.api.models import (
    LevelResponse,
    LevelUpRequest,
    LevelUpResponse,
    UpgradeOptionResponse,
)
from sender_frenz.character_builder.catalog import SKIN_CATALOG
from sender_frenz.common.config import GamePace
from sender_frenz.common.levels import (
    LevelConfig,
    apply_level_up,
    is_level_up_available,
    room_options_for_level,
    skin_options_for_level,
)
from sender_frenz.common.types import AvatarId, Timestamp
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.persistence.store import StoreProtocol
from sender_frenz.space_builder.catalog import ROOM_CATALOG

router = APIRouter()


@router.post("/level-up")
async def level_up_endpoint(
    request_body: LevelUpRequest,
    avatar_id: Annotated[AvatarId, Depends(get_avatar_id)],
    store: Annotated[StoreProtocol, Depends(get_store)],
    pace: Annotated[GamePace, Depends(get_pace)],
    now: Annotated[Timestamp, Depends(get_now)],
) -> LevelUpResponse:
    """Apply a level-up choice and return the new level state.

    Validates that the avatar qualifies for a level-up, applies the chosen
    skin and room upgrades via :func:`~sender_frenz.common.levels.apply_level_up`,
    resets ``sustained_since`` to ``None`` (the streak resets after levelling),
    saves the updated snapshot, and returns available options at the new level.

    Args:
        request_body: ``{ skin_slug, room_slug }`` selections.
        avatar_id: Parsed from the ``Avatar-Id`` request header.
        store: Snapshot store dependency.
        pace: Game pace dependency.
        now: Current timestamp dependency.

    Returns:
        A :class:`~sender_frenz.api.models.LevelUpResponse` with the incremented
        level and available upgrade options.

    Raises:
        :class:`~fastapi.HTTPException` (409): If the avatar does not currently
            qualify for a level-up.
        :class:`~fastapi.HTTPException` (422): If either slug is invalid for the
            current level.
    """
    snapshot = store.load(avatar_id) or make_snapshot(avatar_id, now)

    level_config = LevelConfig.from_pace(pace)
    sustained = snapshot.sustained_since
    if sustained is None or not is_level_up_available(
        snapshot.avatar, sustained, now, level_config
    ):
        raise HTTPException(
            status_code=409, detail="Level-up is not currently available"
        )

    try:
        new_avatar, new_room = apply_level_up(
            avatar=snapshot.avatar,
            room=snapshot.room,
            skin_slug=request_body.skin_slug,
            room_slug=request_body.room_slug,
            skin_catalog=SKIN_CATALOG,
            room_catalog=ROOM_CATALOG,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    updated = GameSnapshot(
        avatar=new_avatar,
        room=new_room,
        history=snapshot.history,
        sustained_since=None,
        last_tick=snapshot.last_tick,
    )
    store.save(updated)

    skin_opts = skin_options_for_level(new_avatar, SKIN_CATALOG)
    room_opts = room_options_for_level(new_room, ROOM_CATALOG)

    return LevelUpResponse(
        avatar_id=str(avatar_id),
        level=LevelResponse(
            current=new_avatar.level.current,
            skin_upgrades=list(new_avatar.level.skin_upgrades),
            room_upgrades=list(new_avatar.level.room_upgrades),
        ),
        skin_options=[
            UpgradeOptionResponse(
                slug=o.slug,
                name=o.name,
                tier=o.tier,
                description=o.description,
            )
            for o in skin_opts
        ],
        room_options=[
            UpgradeOptionResponse(
                slug=o.slug,
                name=o.name,
                tier=o.tier,
                description=o.description,
            )
            for o in room_opts
        ],
    )
