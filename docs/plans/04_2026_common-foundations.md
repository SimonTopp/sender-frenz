# Plan: common — Shared Foundations
**04_2026 · common-foundations**

Status: `PLANNED`
Implements: `src/sender_frenz/common/`
Depends on: nothing (this module is the foundation)
Blocking: all other modules

---

## Goal

Build the shared data layer and rule engines that every other module imports.
Nothing in `common` knows about avatars *doing* things — it only knows what
avatars *are* and what the laws of this world are (how meters decay, how levels
advance). No UI, no I/O, no side effects except where explicitly noted.

---

## Files

### `types.py`

Type aliases and `NewType` wrappers. Imported by every other file in `common`
and by sibling modules.

```
AvatarId   = NewType("AvatarId", UUID)
RoomId     = NewType("RoomId", UUID)
Meter      = float          # 0.0 (empty) → 1.0 (full); never outside this range
Timestamp  = float          # Unix epoch seconds (UTC); use time.time() injection
```

**Protocols** (structural interfaces for type-checker duck-typing):

```
Decayable   — anything with a `meters: dict[str, Meter]` and a `last_updated: Timestamp`
Upgradeable — anything with a `level: int` and an `applied_upgrades: list[str]`
```

Keeping these as protocols (not ABCs) means modules can define their own
dataclasses without importing a base class from `common`.

---

### `models.py`

Pure dataclasses. Frozen where mutation would be a bug. All fields typed.
No methods beyond `__post_init__` validation.

#### `VampiricStage` (enum)

```
NONE      # healthy social state
PALLOR    # early isolation — skin drains, eyes redden
GAUNT     # face sharpens, fingers elongate
HOLLOW    # eye sockets void, lips recede
VAMPIRIC  # full glamour-horror; beautiful and wrong
```

Progression: stages advance with time since last social interaction.
Regression: stages retreat at half the advance rate when interactions resume.

#### `NeedState`

```python
@dataclass(frozen=True)
class NeedState:
    hunger:         Meter        # 1.0 = full, 0.0 = starving
    hygiene:        Meter        # 1.0 = clean, 0.0 = critical
    last_updated:   Timestamp
```

#### `SocialState`

```python
@dataclass(frozen=True)
class SocialState:
    score:           Meter        # 1.0 = thriving, 0.0 = isolated
    vampiric_stage:  VampiricStage
    last_interaction: Timestamp
```

#### `Level`

```python
@dataclass(frozen=True)
class Level:
    current:           int           # 0 = bones; no upper cap enforced here
    skin_upgrades:     tuple[str, ...]   # slugs of chosen skin upgrades, in order
    room_upgrades:     tuple[str, ...]   # slugs of chosen room upgrades, in order
```

#### `Avatar`

```python
@dataclass(frozen=True)
class Avatar:
    id:           AvatarId
    needs:        NeedState
    social:       SocialState
    level:        Level
    created_at:   Timestamp
```

`Avatar` is the single aggregate that all other modules receive and return.
It is immutable — every operation returns a new `Avatar`.

#### `Room`

```python
@dataclass(frozen=True)
class Room:
    id:               RoomId
    avatar_id:        AvatarId
    level:            int            # mirrors Avatar.level.current
    applied_upgrades: tuple[str, ...]  # slugs of chosen room upgrades, in order
```

`Room` is kept separate from `Avatar` intentionally: the space belongs to the
avatar but is its own domain with its own upgrade catalog.

---

### `decay.py`

Pure functions. No randomness. No I/O. Takes state + elapsed time + config,
returns new state. Fully deterministic so tests never need time mocking beyond
passing an explicit `elapsed_seconds` value.

#### `DecayConfig`

```python
@dataclass(frozen=True)
class DecayConfig:
    hunger_rate:   float   # Meter lost per hour; default 0.125 (empties in 8h)
    hygiene_rate:  float   # Meter lost per hour; default 0.0833 (empties in 12h)
    social_rate:   float   # Meter lost per hour; default 0.0417 (empties in 24h)
    vampiric_advance_hours: float  # hours at score=0 before stage advances; default 12
    vampiric_retreat_rate:  float  # stages retreated per hour of interaction; default 0.5
```

Defaults encode the intended game loop rhythm:
- Feed roughly every 8 hours or hunger becomes serious
- Clean every 12 hours
- Interact socially every 24 hours or drift begins

#### Functions

```
apply_need_decay(needs: NeedState, elapsed_seconds: float, config: DecayConfig) -> NeedState
    Clamps results to [0.0, 1.0]. Never raises.

apply_social_decay(social: SocialState, elapsed_seconds: float, config: DecayConfig) -> SocialState
    Also advances vampiric_stage if score hits 0 for long enough.

apply_decay(avatar: Avatar, elapsed_seconds: float, config: DecayConfig) -> Avatar
    Convenience wrapper that applies both and returns a new Avatar.

time_until_critical(meter: Meter, rate_per_hour: float, critical_threshold: float = 0.2) -> float
    Returns seconds until `meter` would cross `critical_threshold` at `rate`.
    Used by the API layer to schedule push notifications.
```

---

### `levels.py`

Level progression rules and upgrade catalog references.

#### Constants

```python
# Combined health score required to unlock a level-up opportunity.
# Combined score = (needs.hunger + needs.hygiene + social.score) / 3
LEVEL_UP_THRESHOLD: Meter = 0.75

# How many hours the combined score must stay above the threshold
# before a level-up is offered. Prevents gaming by momentary spikes.
LEVEL_UP_SUSTAIN_HOURS: float = 4.0
```

#### `UpgradeOption`

```python
@dataclass(frozen=True)
class UpgradeOption:
    slug:        str        # machine-readable identifier; e.g. "torn-hoodie"
    name:        str        # display name; e.g. "Civic Ruin"
    tier:        int        # minimum level required; 0-indexed
    description: str        # flavor text; must pass aesthetic guide checklist
```

#### Functions

```
combined_health(avatar: Avatar) -> Meter
    Returns (hunger + hygiene + social_score) / 3.

is_level_up_available(avatar: Avatar, sustained_since: Timestamp, now: Timestamp) -> bool
    True if combined_health >= LEVEL_UP_THRESHOLD and the duration condition is met.

skin_options_for_level(level: int, catalog: Sequence[UpgradeOption]) -> tuple[UpgradeOption, ...]
    Returns options whose tier <= level and slug not already in avatar.level.skin_upgrades.

room_options_for_level(level: int, catalog: Sequence[UpgradeOption]) -> tuple[UpgradeOption, ...]
    Same pattern for room upgrades.

apply_level_up(avatar: Avatar, room: Room, skin_slug: str, room_slug: str,
               skin_catalog: Sequence[UpgradeOption],
               room_catalog: Sequence[UpgradeOption]) -> tuple[Avatar, Room]
    Validates choices are available, increments level, records slugs.
    Raises ValueError with a descriptive message if either slug is invalid.
```

The actual catalog content (all the skin and room items) lives in
`character_builder/catalog.py` and `space_builder/catalog.py`. `common/levels.py`
only defines the rules; it accepts catalogs as arguments so it stays decoupled.

---

## Implementation Order

1. `types.py` — no dependencies; write first
2. `models.py` — depends on `types.py`
3. `decay.py` — depends on `models.py`
4. `levels.py` — depends on `models.py`

Each file gets its tests written before moving to the next.

---

## Test Strategy

All tests live in `tests/common/`. Every function is tested. 100% branch
coverage is required (enforced by CI).

Key test patterns:

- **Decay tests:** pass explicit `elapsed_seconds` — no `time.time()` calls in
  production code, so no mocking needed.
- **Meter boundary tests:** verify `apply_need_decay` never produces values
  outside `[0.0, 1.0]` even with extreme elapsed times.
- **VampiricStage progression:** test each stage transition in isolation.
- **Level-up gating:** test that `is_level_up_available` respects both the
  threshold *and* the sustain duration.
- **Invalid upgrade rejection:** test that `apply_level_up` raises `ValueError`
  for unknown slugs and already-applied slugs.
- **Immutability:** assert that every function returns a new object, not a
  mutated input.

---

## Open Questions

- **Persistence interface:** `common` defines models but not storage. Where
  does serialisation live? Proposal: a `persistence/` module added later that
  knows about both `common` models and the chosen DB. `common` stays clean.
- **Catalog seeding:** The skin and room catalogs are referenced by slug in
  `common` but defined in `character_builder` and `space_builder`. The API
  layer will need to wire these together at startup. Document this in the API
  plan when we get there.
- **Clock injection:** `decay.py` takes `elapsed_seconds` explicitly. The
  caller is responsible for computing `now - last_updated`. The API layer
  handles this; `common` never calls `time.time()` directly. Confirm this
  pattern holds as we build upward.

---

## Definition of Done

- [ ] All four files implemented and passing `ruff`, `mypy`, and `pytest`
- [ ] 100% branch coverage on `tests/common/`
- [ ] Every public symbol has a Google-style docstring
- [ ] This plan updated with `Status: COMPLETE` and any decisions made during
  implementation noted under Open Questions
