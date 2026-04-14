# Platform Roadmap: From Engine to PWA and Beyond

**Status:** ACTIVE
**Written:** April 2026

---

## Current State

All five engine modules are complete and fully tested:

| Module | Status |
|---|---|
| `common` — models, decay, levels, quips | COMPLETE |
| `required_maintenance` — feed, clean, needs | COMPLETE |
| `character_builder` — avatar, appearance, catalog | COMPLETE |
| `space_builder` — room, catalog | COMPLETE |
| `social_maintenance` — interact, history, effects | COMPLETE |

The codebase is 417 tests at 100% coverage: pure functions, no I/O, no side
effects.  Every game mechanic exists and is correct.  Nothing runs yet.

The next phase shifts from *building the engine* to *building the stack that
runs it* — and eventually the clients that players interact with.

---

## Application Stack (Phases 6–8)

### Phase 6 — `game_loop`

The missing composition layer.  All five engine modules produce correct
isolated results; `game_loop` wires them together into a unified session
model.  This is the only module that imports from multiple sibling modules.

Key exports:

- **`process_tick`** — applies time-based decay and returns the new avatar
  state plus a log of what changed (threshold crossings, vampiric stage
  transitions).  The event log is the contract between game logic and the
  display/animation layer: the renderer needs to know *what changed*, not
  just *what is*, to drive animations correctly.
- **`open_session`** — the player-opens-the-app function.  Calls
  `process_tick`, computes all status summaries, checks level-up
  eligibility, collects login and warning quips, and returns a single
  `SessionState` bundle containing everything the display layer needs.

No persistence, no HTTP.  Pure functions, fully testable.

### Phase 7 — `persistence`

Round-trip serialization and a pluggable storage interface.

- **`serialization.py`** — `Avatar`, `Room`, `InteractionHistory`, and the
  `sustained_since` timestamp ↔ plain `dict` / JSON.  Round-trip safe,
  versioned for forward compatibility.
- **`store.py`** — `StoreProtocol` (load/save `GameSnapshot` by avatar ID) +
  `MemoryStore` in-memory implementation.
- **`snapshots.py`** — `GameSnapshot` as the canonical save unit: avatar,
  room, interaction history, last tick timestamp, and `sustained_since` for
  level-up tracking.

The `MemoryStore` is sufficient to run a server in development.  A
database-backed implementation can be added later against the same protocol.

### Phase 8 — `api`

A FastAPI application that exposes the game over HTTP.  Thin layer over
`game_loop` + `persistence`.  The game becomes network-accessible and
testable end-to-end.

Endpoints:

- `POST /session/open` — applies decay, returns `SessionState`
- `POST /action/{kind}` — dispatches FEED, CLEAN, VISIT, GIFT, CHAT
- `POST /level-up` — validates and applies skin + room upgrade choices
- `GET /avatar/{id}` — current snapshot without advancing time

Player identity is a header-supplied ID in Phase 8; no auth in scope.
Backed by `MemoryStore` initially.

Also introduces **Server-Sent Events** for real-time push of game events to
connected clients — used by the PWA to drive animations without polling.
The `GameEvent` log from `process_tick` feeds this stream directly.

---

## Platform Strategy

### PWA-First

The first playable client is a **Progressive Web App**: a link, a browser,
an "Add to Home Screen" prompt.

- Zero app store friction
- Works on any device
- Web push notifications on Android natively; iOS 16.4+ if added to home
  screen
- One web codebase serves as the foundation for everything that follows

The PWA is not a prototype to be thrown away.  It is the primary client.
Native app and widget layers sit on top of it.

### The Additive Enhancement Path

Each step adds capability without replacing what came before:

```
PWA                           →  link on phone, add-to-home-screen
  + Capacitor/Expo wrapper    →  app store listing, proper push, haptics
      + native widget          →  avatar on home screen
          + Live Activities    →  avatar in Dynamic Island / lock screen
```

The Python API is unchanged across every tier.  The web frontend built for
the PWA becomes the web view inside the native wrapper.  Only widget and
Live Activity layers require native code (Swift + Kotlin).

### Native Widgets

Home screen widgets cannot be written in React Native or web technologies.
They require:

- **iOS:** Swift + SwiftUI + WidgetKit.  A separate Xcode target.
- **Android:** Kotlin + Glance.  A separate Gradle module.

This is a Phase N+2 concern.  The widget capability is unlocked by a design
decision made earlier: `AppearanceState` exposes semantic state (enum values,
slugs) that a server-side renderer can turn into a pre-rendered image.  The
widget then fetches that image from the API — reducing the native widget to a
~50-line image display frame.  All visual logic stays in Python.

This "server-rendered image" approach is viable for v1 widgets and deferred
animation.  When richer animation is needed (idle loops, reaction animations),
the native widget layer takes over rendering directly from the `GameEvent`
stream.

---

## Visualization and Animation

### Where It Fits

Visualization is a Phase 9 concern — after the API is running and the game is
playable through plain JSON.  But two design decisions made in Phase 6 ensure
the display layer is never retrofitted:

1. **`GameEvent` log in `TickResult` and `SessionState`** — the event log
   records what *changed* this tick (vampiric advance, threshold crossings,
   level-up newly available), not just what the state is now.  A renderer
   uses this to trigger the right animations, not just draw the current frame.

2. **`AppearanceState` exposes semantic state** — `vampiric_stage` enum,
   `hunger_visual` / `hygiene_visual` literals, `skin_slug`.  Any rendering
   technology (SVG, Canvas, CSS, native) can consume these without further
   processing.  The composite label is a fallback for text-only displays,
   not the primary interface.

### Asset Anchor Points

The skin and room slugs defined in `character_builder.catalog` and
`space_builder.catalog` are the stable identifiers that map to visual assets.
These slugs are locked; asset creators can work against them now.

### Phase Sequence

```
Phase 6  game_loop     ←  GameEvent log established; animation contract defined
Phase 7  persistence   ←  unchanged by visualization concerns
Phase 8  api           ←  SSE stream for real-time event delivery
Phase 9  PWA frontend  ←  appearance rendering, quip display, event animations
Phase 10 native shell  ←  Capacitor/Expo wrapper, push notifications
Phase 11 widget        ←  server-rendered image (Swift/Kotlin thin frame)
Phase 12 Live Activity ←  Dynamic Island / lock screen; iOS only
```

---

## Key Design Constraints Across All Phases

**No cross-module imports outside `common`.**  The `game_loop` module is the
explicit and only exception — it exists to compose the sibling modules.

**Time is always injected.**  No `time.time()` calls inside any module.
`now: Timestamp` is always a parameter.  This keeps every layer testable.

**Slugs are identity.**  Skin and room slugs are the canonical identifiers
for all upgrade choices, serialization, asset lookup, and analytics.  Never
use catalog indices or display names as keys.

**`GameEvent` log is the animation contract.**  The display layer must never
infer "what changed" by diffing state.  The event log is the source of truth
for transitions.

**Server-rendered images are valid widget output.**  The widget does not need
to replicate rendering logic.  The API serves a pre-rendered avatar image for
widget and notification contexts; the widget is a frame.
