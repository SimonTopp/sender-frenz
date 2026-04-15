# Agent Principles for sender-frenz

This file governs how AI agents (Claude Code, GitHub Copilot, and any future
agents) should behave when working in this repository.

---

## Core Philosophy

This repository is **AI-first**. Agents are first-class contributors, not
assistants. Code, tests, and documentation are written with the expectation
that both humans and agents will read and maintain them.

---

## The Zen of Python (applied here)

These principles from PEP 20 guide every decision in this codebase:

- Beautiful is better than ugly.
- Explicit is better than implicit.
- Simple is better than complex.
- Complex is better than complicated.
- Flat is better than nested.
- Sparse is better than dense.
- Readability counts.
- Special cases aren't special enough to break the rules.
- Although practicality beats purity.
- Errors should never pass silently.
- Unless explicitly silenced.
- In the face of ambiguity, refuse the temptation to guess.
- There should be one — and preferably only one — obvious way to do it.
- Now is better than never.
- Although never is often better than *right* now.
- If the implementation is hard to explain, it's a bad idea.
- If the implementation is easy to explain, it may be a good idea.
- Namespaces are one honking great idea — do more of those!

---

## Plans as Documentation

Implementation plans live in `docs/` alongside reference docs and are
**permanent artefacts**, not throwaway notes. They serve as the authoritative
record of *why* a module was designed the way it was. See
[docs/README.md](docs/README.md) for a full table of contents.

### File naming

```
<slug>.md
```

Examples: `common-foundations.md`, `required-maintenance.md`

Slugs are lowercase, hyphen-separated, and describe the feature or module.
No date prefix — git history records when a file was created.

### Plan lifecycle

Every plan has a `Status` field at the top. Valid values:

| Status | Meaning |
|---|---|
| `PLANNED` | Written but implementation not started |
| `IN PROGRESS` | Actively being implemented |
| `COMPLETE` | Fully implemented, tested, and merged |
| `SUPERSEDED` | Replaced by a newer plan (link to replacement) |

Agents must update the `Status` field when they start and finish work on a
plan. Do not delete superseded plans — add a note and link to the replacement.

### When to write a plan

- Before starting any new module or significant sub-feature
- When a non-obvious architectural decision is made mid-implementation
  (add an "Architectural Decisions" section and update status)
- When an open question from a plan is resolved during implementation

### What a plan must include

- **Goal** — one paragraph on what this solves and what it does not
- **Files** — each file with its key types and function signatures (stubs ok)
- **Implementation order** — which files come first and why
- **Test strategy** — patterns and edge cases to cover
- **Open questions** — unresolved decisions, with proposed answers where possible
- **Definition of done** — checklist; mark items complete as they land

### Relationship to code

Plans are not specs that must be followed exactly. If implementation reveals
a better approach, change the code and update the plan. The plan reflects
what was built, not what was originally imagined.

---

## Self-Documenting Repository

The repository documents itself. Agents must uphold this:

1. **Keep docs current.** When you change code that affects documented
   behavior, update the relevant documentation in the same commit or PR.
2. **Inline documentation over external wikis.** Prefer docstrings, type
   annotations, and well-named identifiers over external references.
3. **Code as documentation.** Function and variable names should be so clear
   that a comment is redundant. Add a comment only when the *why* is not
   obvious from the *what*.
4. **AGENTS.md is authoritative.** If behavior described here conflicts with
   something elsewhere, update the other location to match this file (or open
   a PR to update this file if the principle itself needs revisiting).

---

## Tooling

| Tool | Purpose | Command |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/) | Package management, virtualenvs, script running | `uv sync`, `uv add <pkg>`, `uv run <cmd>` |
| [ruff](https://docs.astral.sh/ruff/) | Linting + formatting | `uv run ruff check .`, `uv run ruff format .` |
| [mypy](https://mypy.readthedocs.io/) | Static type checking | `uv run mypy .` |
| [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) | Tests + coverage | `uv run pytest` |

All tool configuration lives in `pyproject.toml`. Do not create separate
`setup.cfg`, `.mypy.ini`, `tox.ini`, or `.flake8` files — keep config
consolidated.

**Installing dev dependencies:**

```bash
uv sync --group dev
```

**Adding a new runtime dependency:**

```bash
uv add <package>
```

**Adding a new dev-only dependency:**

```bash
uv add --group dev <package>
```

---

## Test Coverage

**Target: 100% test coverage.**

Agents must enforce this target actively, not passively:

- **Before finishing any task**, run the full quality gate:

  ```bash
  uv run ruff format --check .
  uv run ruff check .
  uv run mypy .
  uv run pytest
  ```

  `pytest` is configured in `pyproject.toml` to fail if coverage drops below
  100% (`--cov-fail-under=100`), so a passing test run implies full coverage.

- **If coverage drops below 100%**, write the missing tests before marking the
  task complete. Do not defer test writing to a follow-up.
- **New code = new tests.** Every new function, method, class, or module must
  have at least one test covering its primary behavior and one covering its
  edge cases.
- **Bug fixes = regression tests.** Every bug fix must be accompanied by a
  test that would have caught the bug before the fix.
- If you open a PR and coverage is below 100%, explain in the PR description
  exactly which lines are uncovered and why (e.g., platform-specific code,
  abstract base class stubs that cannot be instantiated).

---

## Documentation Freshness

Agents must treat stale documentation as a bug:

1. **When you change a function signature**, update every docstring, README
   section, and type stub that references it.
2. **When you add a feature**, add or update the relevant section in the docs
   before the PR is complete.
3. **When you remove a feature**, delete or clearly mark as deprecated every
   reference to it.
4. **When you notice docs that are out of date** during any task, fix them
   immediately — even if it is outside the scope of your current task. Stale
   docs are worse than no docs because they actively mislead.

---

## Game Pacing and Time Scale

All time-based constants in this game derive from a `GamePace` multiplier
defined in `src/sender_frenz/common/config.py`. Three named instances exist:

| Constant | `time_scale` | Use |
|---|---|---|
| `PRODUCTION_PACE` | `1.0` | Live game |
| `TEST_PACE` | `720.0` | Integration tests / demos (1 real hour ≈ 30 game days) |
| `FAST_TEST_PACE` | `43200.0` | Smoke tests (1 real minute ≈ 30 game days) |

**Rules for agents:**

1. Never hardcode a rate, duration, or threshold that depends on real time.
   Always derive it from a `GamePace` via a `from_pace(pace)` class method.
2. Unit tests that test pure arithmetic may construct configs directly with
   whatever values the test needs. They do not use the named pace instances.
3. Integration and end-to-end tests must use `TEST_PACE` or `FAST_TEST_PACE`,
   never `PRODUCTION_PACE` (which would require real waiting).
4. Application entry points inject `PRODUCTION_PACE` at the top level and
   pass it down. Nothing inside `common` (or any other module) imports a pace
   constant directly — it is always received as a parameter.

This pattern ensures the full game lifecycle can be exercised in automated
tests in under a minute while production behaviour is identical code.

---

## Core Contracts

These contracts recur throughout the codebase. Every agent working in any
layer should understand them before touching related code.

### `sustained_since` — Level-Up Eligibility Window

`sustained_since: Timestamp | None` lives on `GameSnapshot` and tracks when
the avatar *first* crossed the health threshold required to level up.

| State | Value | Meaning |
|---|---|---|
| Below threshold | `None` | Not eligible; timer not running |
| Just crossed threshold | `now` | Eligible; window starts |
| Still above threshold | unchanged (original `now`) | Window continues |
| Drops below threshold | `None` | Eligibility lost; window resets |
| After level-up | `None` | Reset so the next level starts fresh |

A level-up is only allowed when `sustained_since` has been set **and** the
elapsed real time since that value exceeds the configured sustain window (4
real hours at `PRODUCTION_PACE`).  The update logic lives in
`src/sender_frenz/api/_helpers.py::update_sustained_since`.

### `GameEvent` — The Animation Contract

`process_tick` (in `src/sender_frenz/game_loop/tick.py`) returns a `TickResult`
containing a tuple of `GameEvent` instances.  Each event represents a
threshold that was *newly crossed* during the tick — not the current state,
but the change.

```
TickResult.events  →  (GameEvent(kind=GameEventKind.HUNGER_WARNING, timestamp=…), …)
```

This tuple is the **canonical contract between game logic and the display
layer**.  The renderer must never infer "what changed" by diffing state
snapshots.  It reads the event tuple and triggers the corresponding
animation.  `SessionState.events` (returned by `open_session`) carries the
same tuple for replay on session open.

Event kinds and their display implications:

| Kind | Display trigger |
|---|---|
| `hunger_warning` | Amber pulse on hunger meter; avatar nudge |
| `hunger_critical` | Red shake on hunger meter; avatar distress |
| `hygiene_warning` | Amber pulse on hygiene meter |
| `hygiene_critical` | Red shake on hygiene meter |
| `social_warning` | Social bar dim |
| `social_critical` | Social bar critical flash |
| `vampiric_advance` | Stage transition animation (forward) |
| `vampiric_retreat` | Stage transition animation (reverse) |
| `level_up_ready` | Level-up badge appears |

Events fire at most once per threshold crossing per tick.  Both `hunger_warning`
and `hunger_critical` can fire in the same tick if a large time gap causes
the avatar to drop through both thresholds in one `process_tick` call.

### `TYPE_CHECKING` Import Pattern

Many modules use the `TYPE_CHECKING` guard:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sender_frenz.common.types import Timestamp
    from sender_frenz.common.config import GamePace
```

**Why:** `from __future__ import annotations` makes all annotations lazy
strings at runtime, so imports used *only* in annotations do not need to
execute at runtime.  Moving them inside `if TYPE_CHECKING:` satisfies
ruff's `TCH` rule ("move annotation-only imports to TYPE_CHECKING block"),
avoids circular-import risk, and keeps the runtime import graph lean.

**FastAPI exception:** Route handler files and `deps.py` are exempt from this
pattern.  FastAPI calls `get_type_hints()` on dependency functions and route
handlers at startup, which evaluates the string annotations — so those files
need their types importable at runtime.  The `pyproject.toml` ruff config
suppresses `TCH` for these files via `per-file-ignores`:

```toml
[tool.ruff.lint.per-file-ignores]
"src/sender_frenz/api/deps.py" = ["TCH"]
"src/sender_frenz/api/routes/*.py" = ["TCH"]
```

If you add a new FastAPI route file, add it to that list.

---

## AI-First Development Practices

1. **Readable by agents and humans alike.** Write code that is unambiguous to
   a language model reading it without broader context. Avoid overly terse
   abbreviations, magic numbers, and implicit state.
2. **Structured data over prose config.** Use typed dataclasses, Pydantic
   models, or similar structures rather than untyped dictionaries or
   free-form strings where possible.
3. **Deterministic by default.** Randomness, external API calls, and
   time-dependent logic must be injectable so tests can control them.
4. **Small, pure functions.** Prefer functions that take explicit inputs and
   return explicit outputs with no side effects. Side effects belong at the
   edges of the system.
5. **Fail loud.** Raise exceptions with descriptive messages rather than
   returning sentinel values like `None` or `-1` for error states.

---

## Aesthetic

**Before generating any player-facing content, read [`docs/aesthetic.md`](docs/aesthetic.md) in full.**

This includes: quips, system messages, achievement text, skin names, room item
names, UI copy, flavor text, and any other text or visual element a player will
encounter.

The short version (not a substitute for reading the full guide):

- The game looks like a **corrupted 8-bit arcade cabinet**: pixel art, CRT
  scanlines, neon on black, glitch effects.
- The aesthetic is **cyberpunk + horror**, always both, never just one.
- The game is narrated by **THE SYSTEM** — a gleefully corporate, self-aware,
  slightly menacing AI that treats player suffering as *engagement metrics*.
  Its voice is the *Dungeon Crawler Carl* dungeon system: sarcastically helpful,
  clinically warm, genuinely off.
- System announcements are **ALL CAPS**. Flavor text is mixed case.
- No emoji. No sincere exclamation points. No explained jokes.
- Skins and room items follow a two-word naming convention and a level-tier
  progression arc described in the guide.

`docs/aesthetic.md` is the authoritative source. If this summary conflicts with
it, the full guide wins. Update this summary if the full guide changes.

---

## Agent Workflow Checklist

Before marking any task complete, an agent must verify:

- [ ] `uv run ruff format --check .` passes (no formatting violations)
- [ ] `uv run ruff check .` passes (no lint violations)
- [ ] `uv run mypy .` passes (no type errors)
- [ ] `uv run pytest` passes, including 100% coverage gate
- [ ] Any changed or added public interface has a docstring
- [ ] Any documentation that references changed behavior has been updated
- [ ] The commit message clearly describes *why* the change was made
- [ ] Any player-facing content follows `docs/aesthetic.md`
- [ ] If a plan exists for this work, its `Status` and open questions are updated

---

## Commit Message Convention

```
<type>: <short imperative summary>

<optional body explaining why, not what>
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`

Example:

```
feat: add user age validation

Age must be a positive integer. Negative and zero values previously
caused a silent failure downstream; this surfaces the error early.
```

---

## License

This repository is licensed under the GNU General Public License v3.
All contributions must be compatible with GPL-3.0.
