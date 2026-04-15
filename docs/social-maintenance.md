# Plan: social_maintenance — Social Health Engine

**Status:** COMPLETE
**Written:** April 2026

---

## Goal

Implement the `social_maintenance` package: the layer governing the social
dimension of avatar health.  Physical care alone keeps an avatar alive but
visually gaunt and vampiric; sustained social interaction pushes the avatar
toward a healthy, expressive appearance.

This module does **not** handle persistence, rendering, or physical needs.
It answers three questions: *how do I record a social interaction?*, *what
interactions has this avatar had recently?*, and *what does the social health
state look like right now?*

After this phase all five modules are complete and the full Tend → Connect →
Thrive loop is implemented in pure logic, ready for an application layer to
wire together.

---

## Cross-cutting change: extend `common/quips.py`

`interactions.py` needs quip triggers for successful social interactions.
The existing `QuipTrigger` only covers the negative side (`SOCIAL_WARNING`,
`SOCIAL_CRITICAL`).  Three positive triggers must be added:

```python
VISIT = "visit"   # avatar visited or received a visitor
GIFT  = "gift"    # gift sent or received
CHAT  = "chat"    # message sent or received
```

Each trigger gets 3+ quips in `_QUIPS`, following the aesthetic guide's
social-interaction tone: clinical warmth, faintly surprised the interaction
occurred, mildly suspicious of the player's motives.

**`tests/common/test_quips.py` must also be updated.**  The
`test_all_expected_triggers_defined` test hardcodes the full trigger set;
VISIT, GIFT, and CHAT must be added to the `expected` set.  All other
coverage tests (`test_quip_pool_covers_every_trigger`,
`test_each_pool_has_at_least_three_quips`, `test_returns_string_for_every_trigger`)
automatically cover the new triggers with no changes required.

---

## Files

### `src/sender_frenz/social_maintenance/interactions.py`

The social action layer; mirrors `required_maintenance/actions.py`.

```python
class InteractionKind(StrEnum):
    VISIT = "visit"   # largest boost
    GIFT  = "gift"    # mid boost
    CHAT  = "chat"    # smallest boost

VISIT_SCORE_BOOST: float = 0.25
GIFT_SCORE_BOOST:  float = 0.15
CHAT_SCORE_BOOST:  float = 0.05

@dataclass(frozen=True)
class InteractionResult:
    avatar: Avatar
    quip: str

def interact(
    avatar: Avatar,
    kind: InteractionKind,
    now: Timestamp,
    quip_caller: QuipCaller,
) -> InteractionResult:
    # Boost social.score by kind's boost amount, clamped to 1.0.
    # Set social.last_interaction = now.
    # Quip trigger maps directly to InteractionKind.value (VISIT/GIFT/CHAT).
    # Vampiric stage is NOT modified here — retreat is the decay engine's job.
    # No over-socialization penalty; score simply clamps at 1.0.
```

**Vampiric retreat is not triggered here.**  When `social.score` goes above
zero the existing `apply_social_decay()` in `common/decay.py` computes
retreat on the next tick based on elapsed time.  `interact()` only boosts the
score and stamps `last_interaction`.

### `src/sender_frenz/social_maintenance/history.py`

Per-avatar interaction history.  `InteractionHistory` is a **standalone
frozen structure**, not embedded in `Avatar`.  The application layer holds it
alongside the avatar; `common/models.py` is not changed.

```python
@dataclass(frozen=True)
class InteractionEvent:
    kind: InteractionKind
    timestamp: Timestamp

@dataclass(frozen=True)
class InteractionHistory:
    events: tuple[InteractionEvent, ...]
    # Events stored newest-first so recent_events can short-circuit.

def create_history() -> InteractionHistory:
    # Empty history; the starting state for a new avatar.

def add_event(
    history: InteractionHistory,
    kind: InteractionKind,
    now: Timestamp,
) -> InteractionHistory:
    # Prepend new event; returns a new immutable instance.

def recent_events(
    history: InteractionHistory,
    since: Timestamp,
) -> tuple[InteractionEvent, ...]:
    # All events with timestamp > since, newest first.

def interactions_in_window(
    history: InteractionHistory,
    since: Timestamp,
) -> int:
    # Count of events with timestamp > since.
    # Used by the game loop to gate achievements or notifications.
```

### `src/sender_frenz/social_maintenance/effects.py`

Social health summary and vampiric-stage labels.  The social equivalent of
`required_maintenance/needs.py`'s `NeedsSummary`.

The stub docstring says effects is "consumed by `character_builder.appearance`"
— this means the **application layer** feeds `SocialSummary` data to the
display layer.  No direct import between the two modules; the
no-cross-module-imports rule is preserved.

```python
ISOLATION_THRESHOLD: float = 0.20
    # Score at or below this value is "isolated".
    # Mirrors HUNGER_CRITICAL / HYGIENE_CRITICAL in required_maintenance.

THRIVING_THRESHOLD: float = 0.75
    # Score above this value is "thriving".
    # Aligns with the level-up combined health threshold in common.levels.

@dataclass(frozen=True)
class SocialSummary:
    score: float
    vampiric_stage: VampiricStage
    is_isolated: bool   # score <= ISOLATION_THRESHOLD
    is_thriving: bool   # score > THRIVING_THRESHOLD
    stage_label: str    # THE SYSTEM clinical designation for current stage

def social_summary(avatar: Avatar) -> SocialSummary:
```

`stage_label` maps each `VampiricStage` to a short THE SYSTEM designation:

| Stage | Label |
|---|---|
| NONE | `"NOMINAL"` |
| PALLOR | `"PALLOR ONSET"` |
| GAUNT | `"STRUCTURAL DRIFT"` |
| HOLLOW | `"OCULAR VOID"` |
| VAMPIRIC | `"FULL EXPRESSION"` |

---

## Implementation Order

1. **`common/quips.py`** first — adds VISIT, GIFT, CHAT triggers and quip
   pools; unblocks `interactions.py`.  Update `tests/common/test_quips.py`
   in the same step.
2. **`interactions.py`** — depends on new `QuipTrigger` values; mirrors
   `required_maintenance/actions.py`.
3. **`history.py`** — depends only on `InteractionKind` from `interactions.py`
   and `common` types; no other dependencies.
4. **`effects.py`** — depends only on `common`; standalone query layer.

---

## Test Strategy

### `tests/common/test_quips.py` (update)
- Add VISIT, GIFT, CHAT to `expected` in `test_all_expected_triggers_defined`.
- No other changes needed; existing loop tests cover new triggers.

### `tests/social_maintenance/test_interactions.py`
- Constants: VISIT/GIFT/CHAT boost values are correct.
- `interact(VISIT/GIFT/CHAT)` boosts score by the matching amount.
- Score clamped at 1.0 when already near-full.
- `social.last_interaction` updated to `now`.
- Correct `QuipTrigger` fired for each `InteractionKind`.
- `needs`, `level`, `vampiric_stage`, and `created_at` are unchanged.
- `InteractionResult` is a frozen dataclass.

### `tests/social_maintenance/test_history.py`
- `create_history()` returns empty `InteractionHistory`.
- `add_event()` prepends event; original history is unchanged.
- Multiple adds produce correct newest-first ordering.
- `recent_events()` returns only events after `since`.
- `recent_events()` returns empty tuple when no recent events.
- `recent_events()` at boundary (exactly `since`) excluded.
- `interactions_in_window()` correct for zero, one, and many events.
- `InteractionEvent` and `InteractionHistory` are frozen.

### `tests/social_maintenance/test_effects.py`
- `ISOLATION_THRESHOLD == 0.20`, `THRIVING_THRESHOLD == 0.75`.
- `is_isolated` True at/below threshold; False strictly above.
- `is_thriving` True strictly above threshold; False at/below.
- All 5 `VampiricStage` values map to their correct `stage_label`.
- `score` and `vampiric_stage` pass through unchanged.
- `SocialSummary` is a frozen dataclass.
- Integration: fresh avatar (score=1.0, NONE) → thriving, not isolated, NOMINAL.
- Integration: isolated avatar (score=0.0, VAMPIRIC) → isolated, not thriving,
  FULL EXPRESSION.

---

## Open Questions

| Question | Resolution |
|---|---|
| Should `InteractionHistory` be embedded in `Avatar`? | **No.** Keeps `common/models.py` unchanged and the separation clean. The application layer maintains history alongside the avatar. |
| Is there an over-socialization penalty? | **No.** Social score clamps at 1.0; no design requirement for a penalty. |
| Should vampiric retreat fire immediately on `interact()`? | **No.** Retreat is computed by the decay engine on the next tick. `interact()` only boosts score and stamps the timestamp. |
| Does `effects.py` need a `drift_intensity` fractional progress field? | **No.** `VampiricStage` is already the canonical drift state; fractional progress can't be derived from the avatar alone without knowing elapsed time in the current stage. Keep it simple. |

---

## Dependency Summary

| File | Imports from | Changes to existing |
|---|---|---|
| `common/quips.py` | — | +3 triggers, +9 quips |
| `interactions.py` | `common` only | none |
| `history.py` | `common` + `interactions.py` | none |
| `effects.py` | `common` only | none |
| `tests/common/test_quips.py` | — | update `expected` set |

---

## Definition of Done

- [ ] `common/quips.py` extended with VISIT, GIFT, CHAT triggers and quip pools
- [ ] `tests/common/test_quips.py` updated with new trigger names
- [ ] `interactions.py` implemented and noted in `__init__.py`
- [ ] `history.py` implemented and noted in `__init__.py`
- [ ] `effects.py` implemented and noted in `__init__.py`
- [ ] `__init__.py` updated to reflect implemented modules
- [ ] `tests/social_maintenance/test_interactions.py` written; all tests pass
- [ ] `tests/social_maintenance/test_history.py` written; all tests pass
- [ ] `tests/social_maintenance/test_effects.py` written; all tests pass
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run mypy .` passes
- [ ] `uv run pytest` passes at 100% coverage
- [ ] Plan status updated to COMPLETE
