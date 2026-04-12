# sender-frenz

**A social Tamagotchi.** Raise your avatar from bare bones to a thriving,
stylish creature — but only if you care for its body *and* its community.

---

## What It Is

sender-frenz is a persistent, multiplayer creature-raising game layered on top
of a social network. Your avatar starts as a literal skeleton. Feed it, clean
it, and surround it with friends and it grows into something vibrant and
expressive. Neglect its physical needs and it decays. Neglect its social needs
and it drifts toward something gaunt, hollow-eyed, and vampiric.

The game is played in short daily sessions. Absence is forgiven slowly; both
consistent physical care *and* consistent social engagement are required to
thrive.

---

## Core Game Loop

```
Tend      →  meet your avatar's physical needs (hunger, hygiene)
Connect   →  visit other avatars, receive visitors, send gifts
Thrive    →  both meters above the threshold unlocks a level-up
Customize →  choose one skin upgrade and one space upgrade per level
```

These steps repeat. Each level makes your avatar and their room a little more
expressive and a little more uniquely yours.

---

## Avatar Lifecycle

| Physical care | Social care | Result |
|:---:|:---:|---|
| ✓ | ✓ | Healthy, expressive, increasingly stylish |
| ✓ | ✗ | Survives but grows gaunt, pallid, vampiric |
| ✗ | ✓ | Looks sociable but wasted and bony |
| ✗ | ✗ | Withered undead |

Avatars do not die. They degrade visually and expressively, and the degradation
is reversible — but recovery is slower than decline.

### Level-up unlocks

Reaching a combined health threshold triggers a level-up choice:

- **Skin upgrade** — clothing layers, accessories, hair, pigment, expressions
- **Space upgrade** — furniture, lighting, art, plants (bean bag chairs, lava
  lamps, posters, terrariums, etc.)

Choices are permanent. Each level's catalog is a superset of the previous
level's catalog, so players are never forced to give up an earlier style.

---

## Module Overview

```
src/sender_frenz/
│
├── common/               # Shared foundations used by all other modules
│   ├── models.py         # Core dataclasses: Avatar, Room, NeedState, Level
│   ├── decay.py          # Time-based need-decay engine
│   ├── levels.py         # Level thresholds, unlock catalog, progression rules
│   └── types.py          # Type aliases and Protocols shared across modules
│
├── character_builder/    # Avatar creation and appearance management
│   ├── avatar.py         # Avatar factory, initial skeleton state
│   ├── appearance.py     # Appearance model: how stats map to visual state
│   └── catalog.py        # Skin-upgrade catalog keyed by level
│
├── space_builder/        # Room creation and environment management
│   ├── room.py           # Room factory, initial bare-room state
│   └── catalog.py        # Space-upgrade catalog keyed by level
│
├── required_maintenance/ # Physical-needs engine
│   ├── needs.py          # Hunger and hygiene meters, decay schedules
│   └── actions.py        # Feed and clean actions, effect calculations
│
└── social_maintenance/   # Social-health engine
    ├── interactions.py   # Interaction event types, scoring
    ├── history.py        # Per-avatar interaction history and recency decay
    └── effects.py        # How social score maps to vampiric drift
```

### Dependency rules

```
character_builder  ──┐
space_builder      ──┤──▶  common
required_maintenance─┤
social_maintenance ──┘
```

No module other than `common` may import from another non-`common` module.
Cross-cutting workflows (e.g. "process a time tick that affects both needs and
social score") are composed at the application layer, not inside a module.

---

## Technical Stack

| Concern | Tool |
|---|---|
| Language | Python 3.12 |
| Package management | [uv](https://docs.astral.sh/uv/) |
| Linting + formatting | [ruff](https://docs.astral.sh/ruff/) |
| Type checking | [mypy](https://mypy.readthedocs.io/) (strict) |
| Testing + coverage | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) |

All configuration lives in `pyproject.toml`. See `AGENTS.md` for the full
quality-gate commands every contributor (human or AI) must pass before merging.

---

## Getting Started

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (including dev)
uv sync --group dev

# Run the full quality gate
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
```

---

## Development Roadmap

Modules are intended to be developed and shipped incrementally in this order:

1. **`common`** — data models and decay engine first; everything else depends
   on this foundation.
2. **`required_maintenance`** — physical needs are the simplest game mechanic
   and the fastest path to a runnable prototype.
3. **`character_builder`** — avatar creation and appearance state, including
   the vampiric-drift visual model.
4. **`space_builder`** — room state and furnishing system.
5. **`social_maintenance`** — social scoring, interaction events, and the
   full vampiric-drift pipeline.

Each module ships with 100% test coverage before the next module begins.
See `AGENTS.md` for coverage and documentation standards.

---

## License

GNU General Public License v3. See `LICENSE`.
