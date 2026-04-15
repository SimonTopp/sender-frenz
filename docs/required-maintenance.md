# 04/2026 — required_maintenance module

**Status:** COMPLETE

## Goals

Implement the player-facing feed and clean actions, a composable decay
architecture that supports conditional penalty decays (over-nourishment,
over-scrubbing), and THE SYSTEM quip delivery infrastructure.

## Files changed

| File | Change |
|---|---|
| `src/sender_frenz/common/decay.py` | Refactored: composable `Decay` rules replace fixed-rate `DecayConfig` fields |
| `src/sender_frenz/common/quips.py` | New: `QuipTrigger`, `QuipCaller`, `default_quip_caller` |
| `src/sender_frenz/required_maintenance/actions.py` | New: `feed`, `clean`, over-care decay factories |
| `src/sender_frenz/required_maintenance/needs.py` | New: need predicates and `NeedsSummary` |

---

## Design decisions

### Composable decay architecture

`DecayConfig` now holds a `tuple[Decay, ...]` instead of three fixed-rate
float fields.  Each `Decay` rule carries a `condition: DecayCondition`
predicate evaluated against the current `Avatar` at decay time.

```python
DecayCondition = Callable[[Avatar], bool]

@dataclass(frozen=True)
class Decay:
    name: str
    meter: str           # "hunger", "hygiene", or "social"
    rate_per_hour: float
    condition: DecayCondition
```

Base rules use `_always_active` (unconditionally `True`).  Over-care rules
use named condition functions that check whether a meter exceeds its ideal
maximum.  `DecayCondition` is a plain `Callable` type alias — named functions
satisfy mypy strict without additional hints.

`DecayConfig.effective_rate(avatar, meter)` sums only the active rules:

```python
return sum(
    d.rate_per_hour
    for d in self.decays
    if d.meter == meter and d.condition(avatar)
)
```

Over-care rules are **not** baked into `DecayConfig.from_pace`; they are
injected via `extra_decays` so the application layer opts in explicitly:

```python
config = DecayConfig.from_pace(
    pace,
    extra_decays=(over_nourished_decay(pace), over_scrubbed_decay(pace)),
)
```

### Ideal-maximum model

| Meter | Ideal max | Constant |
|---|---|---|
| Hunger | 0.80 | `HUNGER_IDEAL_MAX` |
| Hygiene | 0.90 | `HYGIENE_IDEAL_MAX` |

Feeding or cleaning past the ideal maximum is allowed — the decay system
handles consequences naturally.  There are no prescriptive cooldowns.

### Over-care decay rates (time_scale = 1.0)

| Rule | Additional rate | Net effect |
|---|---|---|
| `over_nourished_decay` | 1/8 Meter/hour | Doubles hunger drain while over-nourished |
| `over_scrubbed_decay` | 1/12 Meter/hour | Doubles hygiene drain while over-scrubbed |

Both rates scale linearly with `GamePace.time_scale`.

### Quip system

`QuipTrigger` is a `str` `Enum` with eleven values covering every game event
that THE SYSTEM comments on.  `QuipCaller = Callable[[QuipTrigger], str]` is
a plain type alias; `QuipCallerProtocol` is a `runtime_checkable` Protocol
for `isinstance` checks in tests.

`default_quip_caller(rng=None)` returns a closure over an injectable
`random.Random` instance:

- Pass a seeded `random.Random` in tests for deterministic output.
- `None` (default) uses a freshly-created unseeded instance.

Quip pool: ≥ 3 entries per trigger, all written in THE SYSTEM voice
(ALL CAPS announcements, clinical corporate body copy, unsettling closers).

### Action API

`feed(avatar, now, quip_caller)` and `clean(avatar, now, quip_caller)` are
pure functions returning `ActionResult(avatar, quip)`.  The `now: Timestamp`
parameter updates `needs.last_updated` so subsequent decay calculations are
correctly anchored to the action time.

Quip trigger selection:

| Result | Trigger |
|---|---|
| hunger ≤ `HUNGER_IDEAL_MAX` after feed | `QuipTrigger.FEED` |
| hunger > `HUNGER_IDEAL_MAX` after feed | `QuipTrigger.OVER_NOURISHED` |
| hygiene ≤ `HYGIENE_IDEAL_MAX` after clean | `QuipTrigger.CLEAN` |
| hygiene > `HYGIENE_IDEAL_MAX` after clean | `QuipTrigger.OVER_SCRUBBED` |

### Pacing

All time constants derive from `GamePace.time_scale`.  Passing
`PRODUCTION_PACE`, `TEST_PACE`, or `FAST_TEST_PACE` to `from_pace` and the
factory functions is sufficient to switch between real-time and compressed
test cadences.

---

## Implementation notes

- `apply_need_decay` and `apply_social_decay` now take `Avatar` (not
  `NeedState`/`SocialState`) so conditions can read the full avatar state.
- The `Decay` dataclass is `frozen=True`; Python functions are hashable by
  identity so the generated `__hash__` works correctly.
- `over_nourished_decay` and `over_scrubbed_decay` do a local import of
  `Decay` to avoid a circular import between `required_maintenance.actions`
  and `common.decay` at module level.
- All ruff rules pass; mypy strict passes.  Test coverage: 100 % branch.
