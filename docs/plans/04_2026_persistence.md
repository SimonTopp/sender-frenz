# Plan: persistence — Serialization and Storage

**Status:** COMPLETE
**Written:** April 2026

---

## Goal

Implement the `persistence` package: the layer responsible for converting
game state to and from plain dicts / JSON and for storing and retrieving
`GameSnapshot` instances by avatar ID.

This module answers three questions: *how do I turn a snapshot into JSON?*,
*how do I reconstruct a snapshot from JSON?*, and *where do I keep snapshots
between requests?*  It does not schedule decay ticks, serve HTTP requests, or
make decisions about gameplay.

After this phase the API layer (Phase 8) can load a snapshot, pass it to
`game_loop.open_session`, and save the result — completing the full
request/response cycle for a player session.

---

## Dependency Position

```
persistence
  ├── common.models          (Avatar, Room, NeedState, SocialState, Level,
  │                           VampiricStage, vampiric_stage_index,
  │                           vampiric_stage_from_index)
  ├── common.types           (AvatarId, RoomId, Timestamp, Protocol,
  │                           runtime_checkable)
  ├── social_maintenance.history      (InteractionHistory, InteractionEvent,
  │                                    create_history)
  └── social_maintenance.interactions (InteractionKind)
```

`persistence` is an application-stack module (not a game-logic module) and
may import from any sibling.  No sibling game-logic module imports from
`persistence`; it is a one-way dependency.

---

## Files

### `src/sender_frenz/persistence/snapshots.py`

The canonical save unit.  Everything the `game_loop` and `api` layers need
to reconstruct a full session for one avatar.

```python
@dataclass(frozen=True)
class GameSnapshot:
    """Complete persistent state for one avatar.

    Attributes:
        avatar: Current avatar state.
        room: Current room state.
        history: Interaction history log (newest first).
        sustained_since: Timestamp at which the avatar first crossed the
            combined-health threshold in the current level-up streak, or
            ``None`` if the threshold has not been sustained.  The API
            layer updates this on every session (see below).
        last_tick: Unix epoch timestamp of the most recent processed
            tick.  Used by the API layer to compute elapsed time for
            the next call to ``process_tick``.
    """
    avatar: Avatar
    room: Room
    history: InteractionHistory
    sustained_since: Timestamp | None
    last_tick: Timestamp
```

**`sustained_since` update contract (API layer responsibility):**

The API layer computes `sustained_since` after each session and action:

- If `combined_health(new_avatar) >= threshold` and `sustained_since` was
  `None`: set `sustained_since = now`.
- If `combined_health(new_avatar) < threshold`: set `sustained_since = None`.
- After `apply_level_up`: set `sustained_since = None` (streak resets).
- Otherwise: carry `sustained_since` forward unchanged.

This contract is documented here but implemented in Phase 8.

### `src/sender_frenz/persistence/serialization.py`

Pure conversion functions.  No I/O; all functions take Python objects and
return dicts or strings.

```python
_SNAPSHOT_VERSION: int = 1
```

**Avatar round-trip:**

```python
def avatar_to_dict(avatar: Avatar) -> dict[str, Any]:
    # {
    #   "id": str(avatar.id),          # UUID → string
    #   "needs": {
    #       "hunger": float,
    #       "hygiene": float,
    #       "last_updated": float,
    #   },
    #   "social": {
    #       "score": float,
    #       "vampiric_stage": str,      # VampiricStage.name ("NONE", "PALLOR", …)
    #       "last_interaction": float,
    #   },
    #   "level": {
    #       "current": int,
    #       "skin_upgrades": list[str],
    #       "room_upgrades": list[str],
    #   },
    #   "created_at": float,
    # }

def avatar_from_dict(data: dict[str, Any]) -> Avatar:
    # Inverse of avatar_to_dict.
    # VampiricStage: VampiricStage[data["social"]["vampiric_stage"]]
    # skin_upgrades / room_upgrades: tuple(data[…])
    # id: AvatarId(UUID(data["id"]))
```

`VampiricStage` uses `auto()` integer values; serialize by `.name` ("NONE",
"PALLOR", etc.) and deserialize via `VampiricStage[name]` to avoid coupling
to internal integer assignments.

**Room round-trip:**

```python
def room_to_dict(room: Room) -> dict[str, Any]:
    # {
    #   "id": str(room.id),
    #   "avatar_id": str(room.avatar_id),
    #   "level": int,
    #   "applied_upgrades": list[str],
    # }

def room_from_dict(data: dict[str, Any]) -> Room:
```

**InteractionHistory round-trip:**

```python
def history_to_dict(history: InteractionHistory) -> dict[str, Any]:
    # {
    #   "events": [
    #       {"kind": str, "timestamp": float},   # InteractionKind.value
    #       …
    #   ]
    # }
    # InteractionKind is a StrEnum; serialize by .value ("visit", "gift", "chat").

def history_from_dict(data: dict[str, Any]) -> InteractionHistory:
    # Deserialize: InteractionKind(event["kind"])
```

**GameSnapshot round-trip:**

```python
def snapshot_to_dict(snapshot: GameSnapshot) -> dict[str, Any]:
    # {
    #   "version": _SNAPSHOT_VERSION,
    #   "avatar": avatar_to_dict(snapshot.avatar),
    #   "room": room_to_dict(snapshot.room),
    #   "history": history_to_dict(snapshot.history),
    #   "sustained_since": float | None,
    #   "last_tick": float,
    # }

def snapshot_from_dict(data: dict[str, Any]) -> GameSnapshot:
    # Raises ValueError if data["version"] != _SNAPSHOT_VERSION.
    # All sub-deserialization delegates to the typed helpers above.
```

**JSON convenience:**

```python
def snapshot_to_json(snapshot: GameSnapshot) -> str:
    # json.dumps(snapshot_to_dict(snapshot))

def snapshot_from_json(raw: str) -> GameSnapshot:
    # snapshot_from_dict(json.loads(raw))
```

### `src/sender_frenz/persistence/store.py`

Storage interface and in-memory implementation.

```python
@runtime_checkable
class StoreProtocol(Protocol):
    """Read/write interface for game snapshots.

    Implementors provide the actual storage backend (memory, database,
    object store, etc.).  The API layer depends only on this protocol,
    not on any concrete implementation.
    """

    def load(self, avatar_id: AvatarId) -> GameSnapshot | None:
        """Return the snapshot for *avatar_id*, or ``None`` if absent."""
        ...

    def save(self, snapshot: GameSnapshot) -> None:
        """Persist *snapshot*, keyed by ``snapshot.avatar.id``."""
        ...


class MemoryStore:
    """In-memory snapshot store backed by a plain dict.

    Suitable for development, testing, and single-process deployments.
    Not thread-safe; use one instance per process or wrap with a lock
    at the application layer.
    """

    def __init__(self) -> None:
        self._snapshots: dict[AvatarId, GameSnapshot] = {}

    def load(self, avatar_id: AvatarId) -> GameSnapshot | None:
        return self._snapshots.get(avatar_id)

    def save(self, snapshot: GameSnapshot) -> None:
        self._snapshots[snapshot.avatar.id] = snapshot
```

---

## Implementation Order

1. **`snapshots.py`** — no intra-package dependencies; just the dataclass.
2. **`serialization.py`** — depends on all model types and `snapshots.py`.
3. **`store.py`** — depends on `snapshots.py` and `common.types`.

---

## Test Strategy

### `tests/persistence/test_snapshots.py`

- `GameSnapshot` is a frozen dataclass.
- All five fields present and correctly typed.
- Two snapshots with the same data are equal (frozen dataclass equality).
- `sustained_since=None` is a valid snapshot.

### `tests/persistence/test_serialization.py`

**Avatar:**
- `avatar_to_dict` returns a dict with all expected keys.
- `avatar_from_dict(avatar_to_dict(avatar)) == avatar` (round-trip).
- UUID round-trips through string correctly.
- All five `VampiricStage` values serialize and deserialize correctly.
- `skin_upgrades` and `room_upgrades` round-trip as tuples.

**Room:**
- `room_to_dict` / `room_from_dict` round-trip.
- `applied_upgrades` round-trips as tuple.

**InteractionHistory:**
- Empty history round-trips.
- History with one event round-trips.
- History with mixed `InteractionKind` values round-trips (VISIT, GIFT,
  CHAT all serialize and deserialize correctly).
- Newest-first ordering preserved through round-trip.

**GameSnapshot:**
- `snapshot_to_dict` output contains `"version"` key equal to
  `_SNAPSHOT_VERSION`.
- Full round-trip: `snapshot_from_dict(snapshot_to_dict(s)) == s`.
- `sustained_since=None` round-trips as `None`.
- `sustained_since=<float>` round-trips as the same float.
- `snapshot_from_dict` raises `ValueError` on unknown version.

**JSON:**
- `snapshot_from_json(snapshot_to_json(s)) == s` (full JSON round-trip).
- Output of `snapshot_to_json` is a valid JSON string.

### `tests/persistence/test_store.py`

**StoreProtocol:**
- `MemoryStore` satisfies `isinstance(store, StoreProtocol)`.

**MemoryStore.load:**
- Returns `None` for unknown `avatar_id`.
- Returns snapshot after `save`.
- Returns `None` for a different `avatar_id` after saving one snapshot.

**MemoryStore.save:**
- Overwrites existing snapshot for the same `avatar_id`.
- Two snapshots with different `avatar_id`s are stored and retrieved
  independently.

---

## Open Questions

| Question | Resolution |
|---|---|
| Should `snapshot_from_dict` attempt migration on old versions? | **No.** Raise `ValueError` with the version number and let the caller decide. Migration is a Phase 9 concern if needed at all. |
| Should `MemoryStore` be a dataclass? | **No.** It is mutable (not frozen) and its `__init__` sets up a plain dict. A regular class with `__init__` is cleaner than a mutable dataclass. |
| Should private sub-serializers (`_needsstate_to_dict` etc.) be exported? | **No.** They are internal helpers; only the six public functions are part of the API. |
| Should `snapshot_to_json` accept `indent` for pretty-printing? | **No.** Compact JSON is the default; callers can use `json.dumps(snapshot_to_dict(s), indent=2)` directly if needed. |
| Should `RoomId` be validated against the avatar's `room.avatar_id` on load? | **No.** The store is a dumb key-value map; relational integrity is an application-layer concern. |

---

## Dependency Summary

| File | Imports from |
|---|---|
| `snapshots.py` | `common.models`, `common.types`, `social_maintenance.history` |
| `serialization.py` | `common.models`, `common.types`, `persistence.snapshots`, `social_maintenance.history`, `social_maintenance.interactions` |
| `store.py` | `common.types`, `persistence.snapshots`, `typing` |

---

## Definition of Done

- [x] `snapshots.py` implemented and noted in `__init__.py`
- [x] `serialization.py` implemented and noted in `__init__.py`
- [x] `store.py` implemented and noted in `__init__.py`
- [x] `tests/persistence/test_snapshots.py` written; all tests pass
- [x] `tests/persistence/test_serialization.py` written; all tests pass
- [x] `tests/persistence/test_store.py` written; all tests pass
- [x] `uv run ruff format --check .` passes
- [x] `uv run ruff check .` passes
- [x] `uv run mypy .` passes
- [x] `uv run pytest` passes at 100% coverage
- [x] Plan status updated to COMPLETE
