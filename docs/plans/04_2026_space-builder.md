# Plan: space_builder — Room Creation and Upgrade Catalog

**Status:** COMPLETE
**Written:** April 2026

---

## Goal

Implement the `space_builder` package: the layer responsible for creating new
rooms and providing the room upgrade catalog consumed by the level-up flow.

This module is the spatial counterpart to `character_builder`.  It does **not**
handle room rendering, room decay, or social interactions.  It answers two
questions: *how do I make a new room?* and *which room upgrades are available
at a given level?*

With this module in place, `apply_level_up()` in `common.levels` can be
exercised end-to-end using both the skin and room catalogs simultaneously.

`social_maintenance` is out of scope and remains a stub.

---

## Files

### `src/sender_frenz/space_builder/room.py`

Room factory and bare-room constants.

```python
BARE_ROOM_LEVEL: int = 0
    # The level all newly created rooms start at.

def create_room(room_id: RoomId, avatar_id: AvatarId) -> Room:
    # Return Room(id=room_id, avatar_id=avatar_id,
    #             level=BARE_ROOM_LEVEL, applied_upgrades=())
    # No timestamp parameter — Room has no time-based state.
```

### `src/sender_frenz/space_builder/catalog.py`

The room upgrade catalog.  Provides the authoritative list of `UpgradeOption`
instances that `common.levels.room_options_for_level` and
`common.levels.apply_level_up` consume.

```python
ROOM_CATALOG: tuple[UpgradeOption, ...]
    # 12 entries ordered by tier then position.
    # Tier 1 → levels 1-3  (squat / scavenged)
    # Tier 2 → levels 4-6  (hacker den)
    # Tier 3 → levels 7-10 (stylish and wrong)
    # Tier 4 → levels 11+  (void palace / cozy-sinister)

def rooms_for_level(level: int) -> tuple[UpgradeOption, ...]:
    # Return all rooms whose tier <= level.
    # Does NOT filter already-applied slugs; that is levels.room_options_for_level's job.
```

Tier boundary constants mirror those in `character_builder.catalog`.  They are
duplicated rather than imported to respect the no-cross-module-imports rule.

---

## Implementation Order

1. **`catalog.py`** first — no intra-package dependencies; provides the catalog
   content needed for integration tests.
2. **`room.py`** — depends only on `common`; standalone factory.

---

## Test Strategy

### `test_room.py`
- `create_room` preserves `room_id` and `avatar_id`.
- `level` equals `BARE_ROOM_LEVEL` (0).
- `applied_upgrades` is an empty tuple.
- `BARE_ROOM_LEVEL == 0` constant.
- Room is a frozen dataclass (immutability test).
- Two calls with different IDs produce independent rooms.

### `test_catalog.py`
- `ROOM_CATALOG` non-empty; all slugs unique; all tiers positive.
- Two-word naming convention holds for every entry.
- Slugs are lowercase hyphenated.
- Entries ordered by tier (non-decreasing).
- `rooms_for_level` boundary tests: 0, 1, 3, 4, 6, 7, 10, 11, 100.
- Return type always `tuple`; count never decreases with increasing level.
- Tier coverage: at least one entry per tier level.
- Integration: `ROOM_CATALOG` accepted by `levels.room_options_for_level()`.
- Integration: `apply_level_up` succeeds using both `SKIN_CATALOG` and
  `ROOM_CATALOG` together (end-to-end level-up loop).

---

## Open Questions

| Question | Resolution |
|---|---|
| Does `create_room` need a `now` timestamp? | **No.** `Room` has no time-based fields; timestamps would be unused noise. |
| Should tier boundaries be shared with `character_builder`? | **No.** Duplicated locally per the no-cross-module-imports rule. If a third module needs them, promote to `common`. |
| Is a room "appearance" model needed? | **No.** The room's visual state is its `applied_upgrades` list; a display layer can map slugs to visuals without an intermediate model. |

---

## Definition of Done

- [x] `room.py` implemented and noted in `__init__.py`
- [x] `catalog.py` implemented and noted in `__init__.py`
- [x] `__init__.py` updated to reflect implemented modules
- [x] `tests/space_builder/test_room.py` written; all tests pass
- [x] `tests/space_builder/test_catalog.py` written; all tests pass
- [x] `uv run ruff format --check .` passes
- [x] `uv run ruff check .` passes
- [x] `uv run mypy .` passes
- [x] `uv run pytest` passes at 100% coverage
- [x] Plan status updated to COMPLETE
