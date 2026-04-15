# Plan: game_loop — Session and Tick Engine

**Status:** COMPLETE
**Written:** April 2026

---

## Goal

Implement the `game_loop` package: the layer that composes all five engine
modules into a unified session model.  This is the first module that
intentionally imports from multiple sibling packages — it exists precisely
to be the composition point.

`game_loop` answers two questions: *what happened while the player was away?*
(`process_tick`) and *what does the player see when they open the app?*
(`open_session`).

This module is also where the **animation contract is established**.  By
recording what *changed* during a tick — not just what the state is now —
`TickResult` and `SessionState` give the display layer everything it needs to
drive state-transition animations without diffing.

---

## Dependency Position

```
game_loop
  ├── common.decay           (apply_need_decay, apply_social_decay, DecayConfig)
  ├── common.levels          (is_level_up_available, LevelConfig)
  ├── character_builder.appearance  (compute_appearance)
  ├── required_maintenance.needs    (needs_summary)
  └── social_maintenance.effects    (social_summary)
```

`game_loop` is the only package permitted to import from multiple non-`common`
siblings.  No other package imports from `game_loop`.

---

## Files

### `src/sender_frenz/game_loop/tick.py`

The headless state-advancement layer.  Used directly by the persistence /
scheduling layer to advance an avatar's state between sessions.

```python
class GameEventKind(StrEnum):
    VAMPIRIC_ADVANCE  = "vampiric_advance"   # stage worsened this tick
    VAMPIRIC_RETREAT  = "vampiric_retreat"   # stage improved this tick
    HUNGER_WARNING    = "hunger_warning"     # hunger crossed into hungry zone
    HUNGER_CRITICAL   = "hunger_critical"   # hunger crossed into starved zone
    HYGIENE_WARNING   = "hygiene_warning"   # hygiene crossed into unkempt zone
    HYGIENE_CRITICAL  = "hygiene_critical"  # hygiene crossed into grimy zone
    SOCIAL_WARNING    = "social_warning"    # social crossed below thriving threshold
    SOCIAL_CRITICAL   = "social_critical"   # social crossed below isolation threshold
    LEVEL_UP_READY    = "level_up_ready"    # newly eligible this tick (unused in tick;
                                            # emitted by open_session)


@dataclass(frozen=True)
class GameEvent:
    kind: GameEventKind
    timestamp: Timestamp   # always the `now` value passed to process_tick


@dataclass(frozen=True)
class TickResult:
    avatar: Avatar
    events: tuple[GameEvent, ...]   # what changed; newest-first convention


def process_tick(
    avatar: Avatar,
    now: Timestamp,
    pace: GamePace,
) -> TickResult:
    # 1. Compute elapsed time separately for needs and social — their
    #    last-updated timestamps differ.
    #      needs_elapsed  = now - avatar.needs.last_updated
    #      social_elapsed = now - avatar.social.last_interaction
    # 2. Build DecayConfig from pace.
    # 3. Apply apply_need_decay (needs_elapsed) and apply_social_decay
    #    (social_elapsed) independently; assemble new Avatar.
    # 4. Compare before and after to detect threshold crossings and
    #    vampiric stage changes → tuple[GameEvent, ...].
    # 5. Return TickResult(new_avatar, events).
```

**Why separate elapsed values?**  `apply_decay()` in `common.decay` is a
convenience wrapper that passes one elapsed value to both subsystems.
`process_tick` uses `apply_need_decay` and `apply_social_decay` directly
so that a player who ate an hour ago but last interacted socially three days
ago accumulates the correct decay on each meter independently.

**Threshold alignment for event detection:**

| Event kind | Threshold | Alignment |
|---|---|---|
| `HUNGER_WARNING` | hunger < 0.50 | `nourished → hungry` zone boundary |
| `HUNGER_CRITICAL` | hunger < 0.20 | `hungry → starved` zone boundary |
| `HYGIENE_WARNING` | hygiene < 0.60 | `clean → unkempt` zone boundary |
| `HYGIENE_CRITICAL` | hygiene < 0.20 | `unkempt → grimy` zone boundary |
| `SOCIAL_WARNING` | social < `THRIVING_THRESHOLD` (0.75) | thriving → middling |
| `SOCIAL_CRITICAL` | social < `ISOLATION_THRESHOLD` (0.20) | middling → isolated |
| `VAMPIRIC_ADVANCE` | `vampiric_stage` index increased | stage got worse |
| `VAMPIRIC_RETREAT` | `vampiric_stage` index decreased | stage improved |

An event is emitted only when the threshold is *newly* crossed — i.e. the
avatar was above the boundary before the tick and at or below it after.
A meter that was already critical before the tick does not re-emit the event.

### `src/sender_frenz/game_loop/session.py`

The player-facing session layer.  Composes `process_tick` with status
summaries, level-up eligibility, and quip collection.

```python
@dataclass(frozen=True)
class SessionState:
    avatar: Avatar
    needs_summary: NeedsSummary
    social_summary: SocialSummary
    appearance: AppearanceState
    level_up_available: bool
    events: tuple[GameEvent, ...]
    quips: tuple[str, ...]   # one per relevant trigger; LOGIN always first


def open_session(
    avatar: Avatar,
    history: InteractionHistory,
    sustained_since: Timestamp | None,
    now: Timestamp,
    pace: GamePace,
    quip_caller: QuipCaller,
) -> SessionState:
    # 1. process_tick(avatar, now, pace) → TickResult
    # 2. needs_summary(tick.avatar)
    # 3. social_summary(tick.avatar)
    # 4. compute_appearance(tick.avatar)
    # 5. If sustained_since is not None:
    #        is_level_up_available(tick.avatar, sustained_since, now, LevelConfig.from_pace(pace))
    #    else: False
    # 6. Collect quips:
    #        - Always fire LOGIN trigger
    #        - Fire HUNGER_WARNING / HUNGER_CRITICAL if those events present
    #        - Fire HYGIENE_WARNING / HYGIENE_CRITICAL if those events present
    #        - Fire SOCIAL_WARNING / SOCIAL_CRITICAL if those events present
    # 7. Return SessionState.
```

**`sustained_since` ownership.**  `is_level_up_available` requires knowing
when the avatar *first* crossed the health threshold in the current streak.
This timestamp cannot be derived from the avatar alone; it is an application-
layer concern tracked in the persistence snapshot.  `open_session` accepts it
as an optional parameter and skips the level-up check when `None`.

---

## Implementation Order

1. **`tick.py`** first — no dependency on `session.py`; yields a testable
   unit independently.
2. **`session.py`** second — depends on `tick.py` and all the status summary
   functions from sibling modules.

---

## Test Strategy

### `tests/game_loop/test_tick.py`

**`GameEvent` / `GameEventKind`:**
- `GameEvent` is a frozen dataclass.
- `GameEventKind` values are strings (StrEnum).
- All eight kinds are defined.

**`process_tick` — decay applied correctly:**
- Returns a new `Avatar` (not the same object).
- Hunger and hygiene decrease proportionally to elapsed time.
- Social score decreases proportionally to elapsed time.
- Elapsed time computed independently: needs from `needs.last_updated`,
  social from `social.last_interaction`.
- `needs.last_updated` and `social.last_interaction` advanced to `now` after
  the tick.
- Pace multiplier scales decay rates correctly.

**`process_tick` — event detection:**
- No events emitted when no threshold is crossed.
- `HUNGER_WARNING` emitted when hunger crosses 0.50 boundary (not re-emitted
  if already below).
- `HUNGER_CRITICAL` emitted when hunger crosses 0.20 boundary.
- `HYGIENE_WARNING` emitted at 0.60 boundary.
- `HYGIENE_CRITICAL` emitted at 0.20 boundary.
- `SOCIAL_WARNING` emitted when social crosses below `THRIVING_THRESHOLD`.
- `SOCIAL_CRITICAL` emitted when social crosses below `ISOLATION_THRESHOLD`.
- `VAMPIRIC_ADVANCE` emitted when stage index increases.
- `VAMPIRIC_RETREAT` emitted when stage index decreases.
- Multiple events emitted in the same tick when multiple thresholds crossed.
- Events all carry `timestamp == now`.
- `TickResult` is a frozen dataclass.

### `tests/game_loop/test_session.py`

**`SessionState` structure:**
- `SessionState` is a frozen dataclass.
- All fields present and correctly typed.

**`open_session` — decay applied:**
- Returned `avatar` differs from input after time passes.

**`open_session` — status summaries:**
- `needs_summary` reflects post-tick avatar state.
- `social_summary` reflects post-tick avatar state.
- `appearance` reflects post-tick avatar state.

**`open_session` — level-up eligibility:**
- `level_up_available` is `False` when `sustained_since` is `None`.
- `level_up_available` is `True` when threshold held long enough.
- `level_up_available` is `False` when threshold not sustained long enough.

**`open_session` — quips:**
- Always includes a quip from the `LOGIN` trigger.
- Includes a quip for each warning/critical event present in `TickResult`.
- Does not include quips for events that did not occur.
- `quips` is a tuple of non-empty strings.

**`open_session` — events passthrough:**
- `events` in `SessionState` equals `events` from `TickResult`.

**Integration scenarios:**
- Fresh avatar (all meters 1.0, zero elapsed time) → no events, not isolated,
  not hungry, no level-up (no `sustained_since`).
- Neglected avatar (large elapsed, low meters) → critical events emitted,
  warning quips present, correct appearance.
- Recovering avatar (positive social, stage > NONE) → `VAMPIRIC_RETREAT`
  event emitted after sufficient time.

---

## Open Questions

| Question | Resolution |
|---|---|
| Should `process_tick` guard against negative elapsed (clock skew)? | Clamp elapsed to `max(0.0, elapsed)` silently; negative elapsed should never mutate state. |
| Should events be emitted if elapsed is zero? | No — a zero-elapsed tick cannot cross any threshold. |
| Should `LEVEL_UP_READY` be a `GameEvent` emitted by `open_session`? | Yes — the display layer needs to know when level-up becomes newly available to trigger the upgrade UI animation. Include it in `SessionState.events` when `level_up_available` transitions from `False` to `True`. This requires comparing pre-tick and post-tick eligibility in `open_session`. |
| Is there an `ActionState` return type for FEED/CLEAN/INTERACT dispatch? | Out of scope for Phase 6. The API layer (Phase 8) can compose the existing module functions directly; a unified dispatcher is not needed until the pattern proves repetitive across multiple call sites. |

---

## Dependency Summary

| File | Imports from |
|---|---|
| `tick.py` | `common.decay`, `common.models`, `common.config`, `common.types` |
| `session.py` | `game_loop.tick`, `common.levels`, `common.quips`, `character_builder.appearance`, `required_maintenance.needs`, `social_maintenance.effects` |

---

## Definition of Done

- [ ] `tick.py` implemented with `GameEventKind`, `GameEvent`, `TickResult`,
      `process_tick`
- [ ] `session.py` implemented with `SessionState`, `open_session`
- [ ] `__init__.py` documents both modules and key exports
- [ ] `tests/game_loop/test_tick.py` written; all tests pass
- [ ] `tests/game_loop/test_session.py` written; all tests pass
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run mypy .` passes
- [ ] `uv run pytest` passes at 100% coverage
- [ ] Plan status updated to COMPLETE
