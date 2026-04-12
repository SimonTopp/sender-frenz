# Plan: common — Shared Foundations
**04_2026 · common-foundations**

Status: `PLANNED` *(amended 04_2026: added pacing model and config.py)*
Implements: `src/sender_frenz/common/`
Depends on: nothing (this module is the foundation)
Blocking: all other modules

---

## Pacing Model

The game has two intentional rhythms that all time-based constants must satisfy:

| Goal | Target | Implication |
|---|---|---|
| Daily engagement | 1–2 check-ins per day | Meters must become urgent within 8–12 hours of neglect |
| Progression feel | ~1 level-up per month | ~30 days of consistent good behaviour per level |

### Production constants (derived)

```
hunger empties in   8h  → rate = 1.0 / 8  = 0.1250 Meter/hour
hygiene empties in 12h  → rate = 1.0 / 12 = 0.0833 Meter/hour
social empties in  24h  → rate = 1.0 / 24 = 0.0417 Meter/hour

vampiric stage advances every 12h at score=0
vampiric stage retreats at 0.5 stages/hour of interaction

level-up threshold:  combined_health ≥ 0.75
level-up sustain:    threshold held for ≥ 4 real hours
→ rough monthly cadence: player must keep all three meters healthy
  for the majority of ~30 days before a level is offered
```

### `time_scale` multiplier

All time-based constants are derived by multiplying base production values by a
`time_scale` factor. `time_scale = 1.0` is production. Higher values compress
game time so the full lifecycle can be exercised quickly.

| Mode | `time_scale` | 1 real hour feels like | Full monthly cycle in |
|---|---|---|---|
| `PRODUCTION_PACE` | `1.0` | 1 game hour | ~30 real days |
| `TEST_PACE` | `720.0` | 30 game days | ~1 real hour |
| `FAST_TEST_PACE` | `43200.0` | ~1.25 game years | ~1 real minute |

`FAST_TEST_PACE` is for automated smoke tests that need to exercise level-up
logic end-to-end without sleeping. Unit tests never use pace — they pass
explicit `elapsed_seconds` and test pure arithmetic.

---

## Goal

Build the shared data layer and rule engines that every other module imports.
Nothing in `common` knows about avatars *doing* things — it only knows what
avatars *are* and what the laws of this world are (how meters decay, how levels
advance). No UI, no I/O, no side effects except where explicitly noted.

---

## Files

### `config.py`

Game-wide pace configuration. The only place where production vs. test timing
is decided. Every other module derives its time constants from a `GamePace`
instance injected at call time — nothing hardcodes a rate.

```python
@dataclass(frozen=True)
class GamePace:
    """Multiplier that scales all time-based game constants.

    time_scale = 1.0  →  production timing
    time_scale > 1.0  →  compressed time (useful for integration tests / demos)
    """
    time_scale: float  # must be > 0.0

# Named instances — import these rather than constructing GamePace directly.
PRODUCTION_PACE  = GamePace(time_scale=1.0)
TEST_PACE        = GamePace(time_scale=720.0)     # 1 real hour ≈ 30 game days
FAST_TEST_PACE   = GamePace(time_scale=43200.0)   # 1 real minute ≈ 30 game days
```

`config.py` has no imports from within `sender_frenz`. It is safe to import
from anywhere.

---

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
    hunger_rate:            float  # Meter lost per hour
    hygiene_rate:           float  # Meter lost per hour
    social_rate:            float  # Meter lost per hour
    vampiric_advance_hours: float  # hours at score=0 before stage advances
    vampiric_retreat_rate:  float  # stages retreated per hour of interaction

    @classmethod
    def from_pace(cls, pace: GamePace) -> "DecayConfig":
        """Derive decay rates from a GamePace multiplier.

        All base rates are calibrated for production timing (time_scale=1.0):
          hunger empties in  8h, hygiene in 12h, social in 24h.
        Higher time_scale compresses these proportionally.
        """
        s = pace.time_scale
        return cls(
            hunger_rate=0.1250 * s,
            hygiene_rate=0.0833 * s,
            social_rate=0.0417 * s,
            vampiric_advance_hours=12.0 / s,
            vampiric_retreat_rate=0.5 * s,
        )
```

Never construct `DecayConfig` directly in application code. Use
`DecayConfig.from_pace(PRODUCTION_PACE)` (or `TEST_PACE` / `FAST_TEST_PACE`).
Unit tests that test pure arithmetic may construct it directly.

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

#### `LevelConfig`

```python
@dataclass(frozen=True)
class LevelConfig:
    threshold: Meter  # combined_health must reach this to qualify; default 0.75
    sustain_hours: float  # hours threshold must be held; default 4.0

    @classmethod
    def from_pace(cls, pace: GamePace) -> "LevelConfig":
        """Derive level-up timing from a GamePace multiplier.

        The threshold is pace-independent (it's a ratio, not a duration).
        The sustain window shrinks with higher time_scale so demo/test runs
        aren't blocked waiting for a 4-hour window.
        """
        return cls(
            threshold=0.75,
            sustain_hours=4.0 / pace.time_scale,
        )
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

is_level_up_available(avatar: Avatar, sustained_since: Timestamp, now: Timestamp,
                      config: LevelConfig) -> bool
    True if combined_health >= config.threshold and (now - sustained_since) >= sustain window.

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
2. `config.py` — depends only on stdlib; defines `GamePace` and named instances
3. `models.py` — depends on `types.py`
4. `decay.py` — depends on `models.py` and `config.py`
5. `levels.py` — depends on `models.py` and `config.py`

Each file gets its tests written before moving to the next.

---

## Test Strategy

All tests live in `tests/common/`. Every function is tested. 100% branch
coverage is required (enforced by CI).

Key test patterns:

- **Pace config tests:** verify that `DecayConfig.from_pace(PRODUCTION_PACE)`
  produces rates matching the documented base values; verify that
  `DecayConfig.from_pace(TEST_PACE)` produces rates exactly `720x` those values.
  Same for `LevelConfig`. Confirm `GamePace(time_scale=0)` raises `ValueError`.
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

- [ ] All five files implemented and passing `ruff`, `mypy`, and `pytest`
- [ ] 100% branch coverage on `tests/common/`
- [ ] Every public symbol has a Google-style docstring
- [ ] This plan updated with `Status: COMPLETE` and any decisions made during
  implementation noted under Open Questions
