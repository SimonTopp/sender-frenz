"""Round-trip serialization for game state.

All functions are pure: they take Python objects and return dicts or
strings.  No I/O, no side effects.

The snapshot format is versioned.  :data:`_SNAPSHOT_VERSION` is
embedded in every serialized snapshot so future schema changes can be
detected and handled explicitly.

Serialization choices
---------------------
- :class:`~sender_frenz.common.models.VampiricStage` is stored by
  ``.name`` (``"NONE"``, ``"PALLOR"``, etc.) rather than ``.value``
  because the stage uses ``auto()`` which assigns opaque integers.
  Names are stable across code reorganization; integers are not.
- :class:`~sender_frenz.social_maintenance.interactions.InteractionKind`
  is stored by ``.value`` (``"visit"``, ``"gift"``, ``"chat"``) because
  it is a ``StrEnum`` whose values are the canonical identifiers.
- :class:`~uuid.UUID` fields are stored as hyphenated strings.
- ``tuple`` fields (upgrades, history events) are stored as JSON arrays
  and reconstructed as tuples on deserialization.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sender_frenz.common.models import (
    Avatar,
    Level,
    NeedState,
    Room,
    SocialState,
    VampiricStage,
)
from sender_frenz.common.types import AvatarId, RoomId
from sender_frenz.persistence.snapshots import GameSnapshot
from sender_frenz.social_maintenance.history import InteractionEvent, InteractionHistory
from sender_frenz.social_maintenance.interactions import InteractionKind

_SNAPSHOT_VERSION: int = 1
"""Version tag embedded in every serialized snapshot dict."""

# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------


def avatar_to_dict(avatar: Avatar) -> dict[str, Any]:
    """Serialize *avatar* to a plain dict.

    Args:
        avatar: Avatar to serialize.

    Returns:
        A JSON-compatible dict.
    """
    return {
        "id": str(avatar.id),
        "needs": {
            "hunger": avatar.needs.hunger,
            "hygiene": avatar.needs.hygiene,
            "last_updated": avatar.needs.last_updated,
        },
        "social": {
            "score": avatar.social.score,
            "vampiric_stage": avatar.social.vampiric_stage.name,
            "last_interaction": avatar.social.last_interaction,
        },
        "level": {
            "current": avatar.level.current,
            "skin_upgrades": list(avatar.level.skin_upgrades),
            "room_upgrades": list(avatar.level.room_upgrades),
        },
        "created_at": avatar.created_at,
    }


def avatar_from_dict(data: dict[str, Any]) -> Avatar:
    """Deserialize an avatar from *data*.

    Args:
        data: Dict produced by :func:`avatar_to_dict`.

    Returns:
        Reconstructed :class:`~sender_frenz.common.models.Avatar`.
    """
    return Avatar(
        id=AvatarId(UUID(data["id"])),
        needs=NeedState(
            hunger=data["needs"]["hunger"],
            hygiene=data["needs"]["hygiene"],
            last_updated=data["needs"]["last_updated"],
        ),
        social=SocialState(
            score=data["social"]["score"],
            vampiric_stage=VampiricStage[data["social"]["vampiric_stage"]],
            last_interaction=data["social"]["last_interaction"],
        ),
        level=Level(
            current=data["level"]["current"],
            skin_upgrades=tuple(data["level"]["skin_upgrades"]),
            room_upgrades=tuple(data["level"]["room_upgrades"]),
        ),
        created_at=data["created_at"],
    )


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------


def room_to_dict(room: Room) -> dict[str, Any]:
    """Serialize *room* to a plain dict.

    Args:
        room: Room to serialize.

    Returns:
        A JSON-compatible dict.
    """
    return {
        "id": str(room.id),
        "avatar_id": str(room.avatar_id),
        "level": room.level,
        "applied_upgrades": list(room.applied_upgrades),
    }


def room_from_dict(data: dict[str, Any]) -> Room:
    """Deserialize a room from *data*.

    Args:
        data: Dict produced by :func:`room_to_dict`.

    Returns:
        Reconstructed :class:`~sender_frenz.common.models.Room`.
    """
    return Room(
        id=RoomId(UUID(data["id"])),
        avatar_id=AvatarId(UUID(data["avatar_id"])),
        level=data["level"],
        applied_upgrades=tuple(data["applied_upgrades"]),
    )


# ---------------------------------------------------------------------------
# InteractionHistory
# ---------------------------------------------------------------------------


def history_to_dict(history: InteractionHistory) -> dict[str, Any]:
    """Serialize *history* to a plain dict.

    Args:
        history: Interaction history to serialize.

    Returns:
        A JSON-compatible dict with an ``"events"`` list, newest first.
    """
    return {
        "events": [
            {"kind": event.kind.value, "timestamp": event.timestamp}
            for event in history.events
        ],
    }


def history_from_dict(data: dict[str, Any]) -> InteractionHistory:
    """Deserialize an interaction history from *data*.

    Args:
        data: Dict produced by :func:`history_to_dict`.

    Returns:
        Reconstructed
        :class:`~sender_frenz.social_maintenance.history.InteractionHistory`.
    """
    events = tuple(
        InteractionEvent(
            kind=InteractionKind(e["kind"]),
            timestamp=e["timestamp"],
        )
        for e in data["events"]
    )
    return InteractionHistory(events=events)


# ---------------------------------------------------------------------------
# GameSnapshot
# ---------------------------------------------------------------------------


def snapshot_to_dict(snapshot: GameSnapshot) -> dict[str, Any]:
    """Serialize *snapshot* to a plain dict.

    The output includes a ``"version"`` key equal to
    :data:`_SNAPSHOT_VERSION`.

    Args:
        snapshot: Snapshot to serialize.

    Returns:
        A JSON-compatible dict.
    """
    return {
        "version": _SNAPSHOT_VERSION,
        "avatar": avatar_to_dict(snapshot.avatar),
        "room": room_to_dict(snapshot.room),
        "history": history_to_dict(snapshot.history),
        "sustained_since": snapshot.sustained_since,
        "last_tick": snapshot.last_tick,
    }


def snapshot_from_dict(data: dict[str, Any]) -> GameSnapshot:
    """Deserialize a snapshot from *data*.

    Args:
        data: Dict produced by :func:`snapshot_to_dict`.

    Returns:
        Reconstructed :class:`GameSnapshot`.

    Raises:
        ValueError: If ``data["version"]`` is not :data:`_SNAPSHOT_VERSION`.
    """
    version = data.get("version")
    if version != _SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version {version!r}. Expected {_SNAPSHOT_VERSION}."
        )
    return GameSnapshot(
        avatar=avatar_from_dict(data["avatar"]),
        room=room_from_dict(data["room"]),
        history=history_from_dict(data["history"]),
        sustained_since=data["sustained_since"],
        last_tick=data["last_tick"],
    )


# ---------------------------------------------------------------------------
# JSON convenience
# ---------------------------------------------------------------------------


def snapshot_to_json(snapshot: GameSnapshot) -> str:
    """Serialize *snapshot* to a compact JSON string.

    Args:
        snapshot: Snapshot to serialize.

    Returns:
        A JSON string suitable for storage or transmission.
    """
    return json.dumps(snapshot_to_dict(snapshot))


def snapshot_from_json(raw: str) -> GameSnapshot:
    """Deserialize a snapshot from a JSON string.

    Args:
        raw: JSON string produced by :func:`snapshot_to_json`.

    Returns:
        Reconstructed :class:`GameSnapshot`.

    Raises:
        ValueError: If the version field is unrecognized.
    """
    return snapshot_from_dict(json.loads(raw))
