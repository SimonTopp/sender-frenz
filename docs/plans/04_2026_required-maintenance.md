# Plan: required_maintenance — Physical Needs Engine
**04_2026 · required-maintenance**

Status: `PLANNED` *(amended 04_2026: composable decays, ideal/max model, QuipCaller)*
Implements: `src/sender_frenz/required_maintenance/`
Depends on: `common` (complete); `common/decay.py` extended (see below)
Blocking: nothing (parallel with `character_builder`, `space_builder`)

---

## Goal

Implement the physical upkeep layer: hunger and hygiene meters, the fixed
restore amounts applied when a player feeds or cleans their avatar, and the
composable decay rules that respond to over-care as well as neglect.

This module does *not* own the decay engine — that lives in `common.decay`
and is applied by the caller (API layer) on each tick.  `required_maintenance`
owns the player-initiated actions and the domain constants that calibrate
healthy vs. unhealthy meter states.

---

## Meter Model: Ideal Range + Max

Every meter has two thresholds:

| Threshold | Value | Meaning |
|---|---|---|
| `IDEAL_MAX` | < 1.0 | Upper bound of the healthy range; being *above* this is too much |
| Hard max | 1.0 | Meter ceiling; values are clamped here |

Being **below** the ideal range → needs attention (avatar looks hungry / dirty).
Being **above** `IDEAL_MAX` → over-cared-for → activates a composable decay.
Being in the ideal range → healthy; no penalty decays fire.

### Production values

```
FEED_RESTORE       = 0.40   # one feed restores 40% of hunger
HUNGER_IDEAL_MAX   = 0.80   # above this, over-nourished decay activates

CLEAN_RESTORE      = 0.50   # one clean restores 50% of hygiene
HYGIENE_IDEAL_MAX  = 0.90   # above this, over-scrubbed decay activates
```

**Why these numbers:**

- Hunger empties in 8 h.  Two feeds/day keeps the meter in the 40–80 % band —
  right at the `HUNGER_IDEAL_MAX` ceiling.  Feeding a third time that day pushes
  above 0.80 and activates the over-nourished decay.
- Hygiene empties in 12 h.  One clean/day keeps the meter in the 50–100 % band.
  `HYGIENE_IDEAL_MAX = 0.90` gives a small buffer before the over-scrubbed
  decay fires.

Restore amounts are **pace-independent** — they are proportions of the meter,
not durations.  Only the decay rates change with `GamePace`.

---

## Composable Decay Architecture

The current `common.decay.DecayConfig` uses fixed rates.  To support
over-care penalties and future decay types, `DecayConfig` needs to become
a **list of composable `Decay` rules** evaluated on each tick.

### Extension to `common/decay.py`

```python
@dataclass(frozen=True)
class Decay:
    """A single composable decay rule.

    Each Decay encapsulates one reason a meter falls.  Rules are evaluated
    independently; all active rules apply simultaneously on each tick.

    Attributes:
        name: Human-readable identifier, e.g. ``"over-nourished"``.
        meter: Which meter this affects: ``"hunger"``, ``"hygiene"``,
            or ``"social"``.
        rate_per_hour: Base depletion rate (Meter/hour) at time_scale=1.0.
            Scaled by GamePace at construction time.
        condition: Called with the current Avatar; returns True when this
            decay should fire.
    """
    name: str
    meter: str
    rate_per_hour: float
    condition: Callable[[Avatar], bool]
```

`DecayConfig` becomes a container of `Decay` instances.  `apply_decay` iterates
the list and sums contributions from all active rules per meter.  Adding a new
decay type is one new `Decay(...)` object — no changes to the engine.

### Standard decay set (production)

```
hunger-baseline     meter=hunger    rate=0.1250/h   condition: always
hygiene-baseline    meter=hygiene   rate=0.0833/h   condition: always
social-baseline     meter=social    rate=0.0417/h   condition: always
over-nourished      meter=hunger    rate=0.0625/h   condition: hunger > HUNGER_IDEAL_MAX
over-scrubbed       meter=hygiene   rate=0.0417/h   condition: hygiene > HYGIENE_IDEAL_MAX
```

The over-care decays are defined in `required_maintenance/actions.py` (since
they depend on the ideal-max constants) and registered with the decay engine
by the API layer at startup alongside the baseline decays.

> **Note:** The vampiric-stage advance logic in `apply_social_decay` is
> specific enough to stay as-is in `common/decay.py`; it does not need
> to be refactored into the composable model yet.

---

## Files

### `actions.py`

Pure functions.  No I/O, no randomness.  Each function takes the current
`Avatar` and a timestamp, returns a new `Avatar`.  No cooldown logic here —
players can act whenever they want; the composable decay system provides the
natural consequence of over-care.

```python
# ---------------------------------------------------------------------------
# Restore amounts — pace-independent proportions of the meter
# ---------------------------------------------------------------------------
FEED_RESTORE:      float = 0.40
CLEAN_RESTORE:     float = 0.50

# ---------------------------------------------------------------------------
# Ideal-max thresholds — above these, over-care decays activate
# ---------------------------------------------------------------------------
HUNGER_IDEAL_MAX:  float = 0.80
HYGIENE_IDEAL_MAX: float = 0.90


def feed(avatar: Avatar, now: Timestamp) -> Avatar:
    """Restore hunger by FEED_RESTORE, clamped to 1.0.

    If the resulting hunger exceeds HUNGER_IDEAL_MAX, the over-nourished
    composable decay will activate on the next tick (handled by the decay
    engine, not by this function).

    Args:
        avatar: Current avatar state.
        now: Timestamp of the feed action; becomes NeedState.last_updated.

    Returns:
        New Avatar with hunger increased by FEED_RESTORE (max 1.0).
    """


def clean(avatar: Avatar, now: Timestamp) -> Avatar:
    """Restore hygiene by CLEAN_RESTORE, clamped to 1.0.

    If the resulting hygiene exceeds HYGIENE_IDEAL_MAX, the over-scrubbed
    composable decay will activate on the next tick.

    Args:
        avatar: Current avatar state.
        now: Timestamp of the clean action; becomes NeedState.last_updated.

    Returns:
        New Avatar with hygiene increased by CLEAN_RESTORE (max 1.0).
    """


def over_nourished_decay(pace: GamePace) -> Decay:
    """Return the composable Decay that fires when hunger > HUNGER_IDEAL_MAX.

    Intended to be registered with the decay engine at startup.

    Args:
        pace: Game pace used to scale the rate.

    Returns:
        A Decay that accelerates hunger depletion when the avatar is over-full.
    """


def over_scrubbed_decay(pace: GamePace) -> Decay:
    """Return the composable Decay that fires when hygiene > HYGIENE_IDEAL_MAX.

    Args:
        pace: Game pace used to scale the rate.

    Returns:
        A Decay that accelerates hygiene depletion when the avatar is
        over-cleaned.
    """
```

---

### `needs.py`

Read-only helpers.  Nothing here mutates anything.

```python
def is_hungry(avatar: Avatar, threshold: float = 0.40) -> bool:
    """Return True if hunger is at or below threshold (default: FEED_RESTORE).

    Args:
        avatar: Current avatar state.
        threshold: Hunger level at or below which the avatar is hungry.

    Returns:
        True if hunger <= threshold.
    """


def is_dirty(avatar: Avatar, threshold: float = 0.50) -> bool:
    """Return True if hygiene is at or below threshold (default: CLEAN_RESTORE).

    Args:
        avatar: Current avatar state.
        threshold: Hygiene level at or below which the avatar is dirty.

    Returns:
        True if hygiene <= threshold.
    """


def is_over_nourished(avatar: Avatar) -> bool:
    """Return True if hunger is above HUNGER_IDEAL_MAX.

    Args:
        avatar: Current avatar state.

    Returns:
        True if hunger > HUNGER_IDEAL_MAX.
    """


def is_over_scrubbed(avatar: Avatar) -> bool:
    """Return True if hygiene is above HYGIENE_IDEAL_MAX.

    Args:
        avatar: Current avatar state.

    Returns:
        True if hygiene > HYGIENE_IDEAL_MAX.
    """


def needs_summary(avatar: Avatar) -> dict[str, float]:
    """Return a plain dict snapshot of current need meter values.

    Args:
        avatar: Current avatar state.

    Returns:
        ``{"hunger": float, "hygiene": float}`` with values in [0.0, 1.0].
        Returns a new dict on each call; safe to mutate.
    """
```

---

## QuipCaller (to be added to `common/quips.py`)

Based on review feedback, quip delivery should be a flexible interface so the
backend (hardcoded catalog now, potentially AI-driven later) can be swapped
without touching callers.

```python
# common/quips.py

class QuipTrigger(str, Enum):
    """All named events that can trigger a THE SYSTEM quip."""
    FEED             = "feed"
    CLEAN            = "clean"
    HUNGER_WARNING   = "hunger_warning"
    HUNGER_CRITICAL  = "hunger_critical"
    HYGIENE_WARNING  = "hygiene_warning"
    HYGIENE_CRITICAL = "hygiene_critical"
    OVER_NOURISHED   = "over_nourished"
    OVER_SCRUBBED    = "over_scrubbed"
    # ... extended as other modules add triggers


class QuipCaller(Protocol):
    """Interface for retrieving a THE SYSTEM quip for a given trigger.

    Implementations may be a hardcoded catalog, a weighted random picker,
    or an AI-backed generator.  Callers never depend on a specific backend.
    """
    def __call__(self, trigger: QuipTrigger) -> str:
        """Return a quip string for trigger.

        Args:
            trigger: The event that occurred.

        Returns:
            A quip string following the aesthetic guide voice rules.
        """
        ...


def default_quip_caller() -> QuipCaller:
    """Return the default hardcoded QuipCaller implementation."""
    ...
```

`QuipCaller` lives in `common` because every module will need it.
`required_maintenance` will be the first module to wire it up.
The `QuipTrigger` enum grows as modules are implemented.

---

## Implementation Order

1. Extend `common/decay.py` — add `Decay` dataclass; update `DecayConfig` to
   hold a list; update `apply_decay` to iterate composable rules
2. Add `common/quips.py` — `QuipTrigger`, `QuipCaller` protocol, hardcoded
   default implementation with at least the triggers above
3. `required_maintenance/actions.py` — `feed`, `clean`, `over_nourished_decay`,
   `over_scrubbed_decay`
4. `required_maintenance/needs.py` — read-only helpers

Each step gets tests before moving to the next.

---

## Test Strategy

### `tests/common/test_decay.py` (additions)

- `Decay` construction and frozen immutability
- `apply_decay` applies all active decays and ignores inactive ones
- `apply_decay` with two rules targeting the same meter sums their contributions
- Over-nourished decay fires when hunger > 0.80, silent otherwise

### `tests/common/test_quips.py` (new)

- `default_quip_caller()` returns a string for every `QuipTrigger` value
- Returned strings are non-empty
- Each call returns *a* string (randomisation tested for type, not value)

### `tests/required_maintenance/test_actions.py`

- `feed` increases hunger by `FEED_RESTORE`
- `feed` on a full avatar clamps hunger at 1.0
- `feed` on an empty avatar sets hunger to exactly `FEED_RESTORE`
- `feed` updates `NeedState.last_updated` to `now`
- `feed` does not change hygiene, social state, or level
- `feed` returns a new `Avatar` instance (immutability)
- `over_nourished_decay` condition returns True above `HUNGER_IDEAL_MAX`, False below
- All of the above mirrored for `clean` / `over_scrubbed_decay`

### `tests/required_maintenance/test_needs.py`

- `is_hungry` True at and below default threshold; False above
- `is_hungry` accepts a custom threshold
- `is_dirty` mirrors for hygiene
- `is_over_nourished` True above `HUNGER_IDEAL_MAX`, False at and below
- `is_over_scrubbed` True above `HYGIENE_IDEAL_MAX`, False at and below
- `needs_summary` returns correct values; returns new dict each call

---

## Open Questions

- **Over-care UX signal:** When the over-nourished decay fires, should the
  API layer serve an `OVER_NOURISHED` quip immediately, or only on the next
  status poll?  Proposal: quip returned as part of the `feed` action response.
- **`Decay.condition` and mypy:** `Callable[[Avatar], bool]` in a frozen
  dataclass may cause issues with mypy's strict mode (lambdas are typed as
  `Callable[..., bool]`).  Consider a named `DecayCondition = Callable[[Avatar],
  bool]` type alias or a simple `Protocol`.
- **Quip randomisation:** Should `default_quip_caller` always return the same
  quip for a trigger (deterministic, easy to test) or pick from a pool
  (better UX)?  Proposal: pool with injectable random seed so tests can fix it.

---

## Definition of Done

- [ ] `common/decay.py` extended with composable `Decay` and updated engine
- [ ] `common/quips.py` added with `QuipTrigger`, `QuipCaller`, default impl
- [ ] `actions.py` implemented and tested
- [ ] `needs.py` implemented and tested
- [ ] 100% branch coverage across all new and modified files
- [ ] `ruff`, `mypy`, `pytest` all pass
- [ ] This plan updated with `Status: COMPLETE`
