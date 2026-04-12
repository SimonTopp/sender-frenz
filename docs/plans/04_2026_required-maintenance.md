# Plan: required_maintenance — Physical Needs Engine
**04_2026 · required-maintenance**

Status: `PLANNED`
Implements: `src/sender_frenz/required_maintenance/`
Depends on: `common` (complete)
Blocking: nothing (parallel with `character_builder`, `space_builder`)

---

## Goal

Implement the physical upkeep layer: hunger and hygiene meters, the fixed
restore amounts applied when a player feeds or cleans their avatar, and the
validation rules that prevent nonsensical inputs.

This module does *not* own decay — that lives in `common.decay` and is applied
by the caller (API layer) on each request.  `required_maintenance` only handles
the player-initiated actions that push meters back up.

---

## Restore Model: Fixed Amounts (Option 1)

Each action restores a fixed proportion of the meter regardless of current
value.  This is the most Tamagotchi-faithful approach: every feed is the same
meal, every clean is the same scrub.  There is no strategy in portion size —
the strategy is *showing up*.

### Production values

```
FEED_RESTORE  = 0.40   # one feed restores 40% of the hunger meter
CLEAN_RESTORE = 0.50   # one clean restores 50% of the hygiene meter
```

**Why these numbers:**

- Hunger empties in 8 h at production pace.  Two feeds/day (every 12 h) leaves
  the avatar at roughly 40 % hunger before each feed.  Restoring 40 % keeps
  the meter in the 40–80 % band with consistent twice-daily play — healthy but
  with real consequences for missing a session.
- Hygiene empties in 12 h.  One clean/day (every 24 h) keeps the avatar at
  roughly 50 % before each clean.  Restoring 50 % keeps the meter in the
  50–100 % band with daily play.

Meters clamp at 1.0; over-restoring is silently capped (feeding a nearly-full
avatar wastes nothing mechanically but doesn't overflow).

### Restore amounts scale with `GamePace`

Like decay rates, restore amounts are **not** pace-dependent — they are
proportions of the meter, not durations.  A feed always restores 40 % of the
hunger meter regardless of `time_scale`.  Only the *frequency* at which the
meter drains changes with pace.

`FEED_RESTORE` and `CLEAN_RESTORE` are therefore plain constants, not derived
from `GamePace`.

---

## Files

### `actions.py`

Pure functions.  No I/O, no randomness.  Each function takes the current
`Avatar` and a timestamp, returns a new `Avatar`.

```python
FEED_RESTORE:  float = 0.40
CLEAN_RESTORE: float = 0.50


def feed(avatar: Avatar, now: Timestamp) -> Avatar:
    """Restore hunger by FEED_RESTORE, clamped to 1.0.

    Args:
        avatar: Current avatar state.
        now: Current timestamp; becomes the new NeedState.last_updated.

    Returns:
        New Avatar with hunger increased by FEED_RESTORE (max 1.0).
    """


def clean(avatar: Avatar, now: Timestamp) -> Avatar:
    """Restore hygiene by CLEAN_RESTORE, clamped to 1.0.

    Args:
        avatar: Current avatar state.
        now: Current timestamp; becomes the new NeedState.last_updated.

    Returns:
        New Avatar with hygiene increased by CLEAN_RESTORE (max 1.0).
    """
```

Both functions update `NeedState.last_updated` to `now`.  The `social` and
`level` fields on the returned `Avatar` are identical to the input.

**No cooldown enforcement here.**  The API layer is responsible for rate-
limiting player actions (e.g. preventing spam-feeding in a loop).
`required_maintenance` is pure domain logic; policy lives at the boundary.

---

### `needs.py`

Read-only helpers that answer questions about the current need state.
Nothing here mutates anything.

```python
def is_hungry(avatar: Avatar, threshold: float = 0.4) -> bool:
    """Return True if hunger is at or below threshold.

    The default threshold (0.4) is the expected pre-feed meter level
    for a player who feeds twice a day on schedule.

    Args:
        avatar: Current avatar state.
        threshold: Hunger level at or below which the avatar is considered hungry.

    Returns:
        True if hunger <= threshold.
    """


def is_dirty(avatar: Avatar, threshold: float = 0.5) -> bool:
    """Return True if hygiene is at or below threshold.

    The default threshold (0.5) is the expected pre-clean meter level
    for a player who cleans once a day on schedule.

    Args:
        avatar: Current avatar state.
        threshold: Hygiene level at or below which the avatar is considered dirty.

    Returns:
        True if hygiene <= threshold.
    """


def needs_summary(avatar: Avatar) -> dict[str, float]:
    """Return a plain dict snapshot of current need meter values.

    Intended for use by the API layer to construct response payloads.
    Returns a new dict on each call; safe to mutate.

    Args:
        avatar: Current avatar state.

    Returns:
        ``{"hunger": float, "hygiene": float}`` with values in [0.0, 1.0].
    """
```

---

## Implementation Order

1. `actions.py` — the core of the module; write and test first
2. `needs.py` — read-only helpers; depends only on `common.models`

---

## Test Strategy

All tests live in `tests/required_maintenance/`.  100% branch coverage required.

### `test_actions.py`

- `feed` increases hunger by `FEED_RESTORE`
- `feed` on a full avatar clamps hunger at 1.0 (no overflow)
- `feed` on an empty avatar sets hunger to exactly `FEED_RESTORE`
- `feed` updates `NeedState.last_updated` to `now`
- `feed` does not change hygiene, social state, or level
- `feed` returns a new `Avatar` instance (immutability)
- All of the above mirrored for `clean` / `CLEAN_RESTORE` / hygiene

### `test_needs.py`

- `is_hungry` returns True at and below threshold (default 0.4)
- `is_hungry` returns False above threshold
- `is_hungry` accepts a custom threshold
- `is_dirty` mirrors `is_hungry` for hygiene (default threshold 0.5)
- `needs_summary` returns correct hunger and hygiene values
- `needs_summary` returns a new dict each call (not a reference to internal state)

---

## Open Questions

- **Cooldown policy:** How often can a player feed/clean per real-world
  period?  Proposal: one feed and one clean per 6-hour window, enforced at
  the API layer.  `required_maintenance` remains policy-free.
- **Partial restore on near-full meter:** Should feeding an avatar at 0.8
  hunger only restore 0.2 (to cap at 1.0), or restore the full 0.4 but cap
  silently?  Current plan: silent cap (simpler, consistent UX — the action
  always "works", it just doesn't help much when nearly full).
- **THE SYSTEM quips:** Where do the quip strings live?  Proposal: a
  `quips/` module (or sub-package) added alongside `common` that other
  modules can import action-specific strings from.  Out of scope for this
  module but worth deciding before `social_maintenance`.

---

## Definition of Done

- [ ] `actions.py` implemented and tested
- [ ] `needs.py` implemented and tested
- [ ] 100% branch coverage on `tests/required_maintenance/`
- [ ] `ruff`, `mypy`, `pytest` all pass
- [ ] Every public symbol has a Google-style docstring
- [ ] This plan updated with `Status: COMPLETE`
