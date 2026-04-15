# Plan: character_builder — Avatar Creation and Appearance

**Status:** COMPLETE
**Written:** April 2026

---

## Goal

Implement the `character_builder` package: the layer responsible for creating
new avatars and computing their visual state from current stats.

This module does **not** handle persistence, rendering, or social interactions.
It answers two questions: *how do I make a new avatar?* and *what does this
avatar look like right now?*  Everything visual that a display layer needs is
captured in `AppearanceState`.

`space_builder` (rooms) and `social_maintenance` (social interactions) are out
of scope here and remain stubs.

---

## Files

### `src/sender_frenz/character_builder/catalog.py`

The skin upgrade catalog.  Provides the authoritative list of `UpgradeOption`
instances that `common.levels.skin_options_for_level` and
`common.levels.apply_level_up` consume.

```python
SKELETON_SKIN_SLUG: str
    # Sentinel slug representing the bare-skeleton base state (no skin applied).
    # Used by appearance.py to identify un-customised avatars.

SKIN_CATALOG: tuple[UpgradeOption, ...]
    # All skin upgrades, ordered by tier then slug.
    # Tier 1 → levels 1–3  (post-collapse streetwear)
    # Tier 2 → levels 4–6  (street cyberpunk)
    # Tier 3 → levels 7–10 (corpo-horror)
    # Tier 4 → levels 11+  (ascended / bio-mechanical)

def skins_for_level(level: int) -> tuple[UpgradeOption, ...]:
    # Return all skins whose tier <= level, ordered by tier then slug.
    # Does NOT filter already-applied slugs; that is levels.skin_options_for_level's job.
```

### `src/sender_frenz/character_builder/avatar.py`

Avatar factory and skeleton-state constants.

```python
SKELETON_LEVEL: int = 0
    # The level all avatars start at.

INITIAL_METER: float = 1.0
    # All need and social meters are set to this on creation (fully topped up).

def create_avatar(avatar_id: AvatarId, now: Timestamp) -> Avatar:
    # Return a new Avatar in skeleton state:
    #   needs.hunger = needs.hygiene = INITIAL_METER
    #   social.score = INITIAL_METER, vampiric_stage = VampiricStage.NONE
    #   level.current = SKELETON_LEVEL, no upgrades
    #   created_at = needs.last_updated = social.last_interaction = now
```

### `src/sender_frenz/character_builder/appearance.py`

Appearance model: maps current avatar stats to a display-ready snapshot.

```python
# Thresholds (mirror required_maintenance constants; no cross-module import)
HUNGER_IDEAL_MAX: float = 0.80   # above this → "over_nourished"
HYGIENE_IDEAL_MAX: float = 0.90  # above this → "over_scrubbed"
HUNGER_CRITICAL: float = 0.20    # at or below → "starved"
HYGIENE_CRITICAL: float = 0.20   # at or below → "grimy"

HungerVisual = Literal["over_nourished", "nourished", "hungry", "starved"]
HygieneVisual = Literal["over_scrubbed", "clean", "unkempt", "grimy"]

@dataclass(frozen=True)
class AppearanceState:
    vampiric_stage: VampiricStage
    hunger_visual: HungerVisual
    hygiene_visual: HygieneVisual
    skin_slug: str | None          # most-recently applied skin, or None
    composite_label: str           # human-readable status, THE SYSTEM voice

def compute_appearance(avatar: Avatar) -> AppearanceState:
    # Pure function.  Derives all fields from avatar state alone.
```

---

## Implementation Order

1. **`catalog.py`** first — no dependencies inside the package; provides the
   `UpgradeOption` catalog that `levels.py` functions consume in tests.
2. **`avatar.py`** next — depends only on `common`; standalone factory.
3. **`appearance.py`** last — depends on `common` types and the threshold
   constants; references `catalog.py` only conceptually (slug passthrough).

---

## Test Strategy

### `test_catalog.py`
- Catalog is non-empty; all slugs are unique; all tiers are positive integers.
- Two-word naming convention holds for every entry (name splits into exactly two
  words when split on whitespace).
- `skins_for_level(0)` returns empty tuple.
- `skins_for_level(1)` returns only tier-1 entries.
- `skins_for_level(3)` still returns only tier-1 (tier-2 requires level 4).
- `skins_for_level(4)` includes tier-1 and tier-2 entries.
- `skins_for_level(100)` returns all entries.
- Return type is always `tuple`.
- Entries within each tier are consistently ordered (stable catalog).

### `test_avatar.py`
- `create_avatar` produces an `Avatar` with the supplied `avatar_id`.
- All meters (`hunger`, `hygiene`, `social.score`) equal `INITIAL_METER`.
- `vampiric_stage` is `VampiricStage.NONE`.
- `level.current` equals `SKELETON_LEVEL` (0).
- `skin_upgrades` and `room_upgrades` are empty tuples.
- `created_at`, `needs.last_updated`, and `social.last_interaction` all equal
  `now`.
- Two calls with different `avatar_id` values produce independent avatars (IDs
  differ; all other fields equal).
- Constants: `SKELETON_LEVEL == 0`, `INITIAL_METER == 1.0`.

### `test_appearance.py`
- `hunger_visual` bucketing: each boundary (≤0.20, 0.21, 0.50, 0.51, 0.80,
  0.81) maps to the correct label.
- `hygiene_visual` bucketing: same boundary approach.
- All five `VampiricStage` values pass through to `AppearanceState.vampiric_stage`.
- `skin_slug` is `None` when no upgrades have been applied.
- `skin_slug` equals the only upgrade slug when one has been applied.
- `skin_slug` equals the *last* slug when multiple upgrades exist.
- `composite_label` is uppercase and contains the hunger and hygiene visuals.
- `composite_label` includes the vampiric stage name when stage is not NONE.
- `composite_label` omits the vampiric stage component when stage is NONE.
- `composite_label` includes the skin slug when one is present.
- `composite_label` omits the skin component when `skin_slug` is None.
- `compute_appearance` returns an `AppearanceState`.
- Full integration: fresh skeleton avatar → expected all-healthy appearance.
- Full integration: fully degraded avatar → expected all-critical appearance.

---

## Open Questions

| Question | Resolution |
|---|---|
| Should `AppearanceState` include the full `skin_upgrades` list or just the active (most recent) slug? | **Most recent only.** The full list is always available via `avatar.level.skin_upgrades`; duplicating it here adds noise. |
| Should `composite_label` follow a strict format or be free-form? | **Strict slash-separated format** so display layers can parse it if needed: `STAGE / HUNGER / HYGIENE` or `HUNGER / HYGIENE / SKIN` depending on what is present. |
| Do thresholds belong in `common`? | **Not yet.** Moving them would require changing `required_maintenance`; the mirroring approach is noted in docstrings and is acceptable until a third consumer appears. |

---

## Definition of Done

- [x] `catalog.py` implemented and exported from `__init__.py`
- [x] `avatar.py` implemented and exported from `__init__.py`
- [x] `appearance.py` implemented and exported from `__init__.py`
- [x] `__init__.py` updated to reflect implemented modules
- [x] `tests/character_builder/test_catalog.py` written; all tests pass
- [x] `tests/character_builder/test_avatar.py` written; all tests pass
- [x] `tests/character_builder/test_appearance.py` written; all tests pass
- [x] `uv run ruff format --check .` passes
- [x] `uv run ruff check .` passes
- [x] `uv run mypy .` passes
- [x] `uv run pytest` passes at 100% coverage
- [x] Plan status updated to COMPLETE
