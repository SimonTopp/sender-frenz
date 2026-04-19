# docs/

Reference documentation and module plans for sender-frenz.

All plans are permanent artefacts — they record *why* things were built the
way they were, not just *what* was built. See [AGENTS.md](../AGENTS.md) for
the plan lifecycle and contribution guidelines.

---

## Reference

| File | What it covers |
|---|---|
| [aesthetic.md](aesthetic.md) | THE SYSTEM voice, visual style, skin/room tier progression, content checklist for agents |
| [platform-roadmap.md](platform-roadmap.md) | Full stack strategy: PWA → Capacitor shell → native widgets → Live Activities |

---

## Module plans

| File | Status | What it covers |
|---|---|---|
| [common-foundations.md](common-foundations.md) | COMPLETE | Core types, models, decay engine, level/upgrade system, quips |
| [required-maintenance.md](required-maintenance.md) | COMPLETE | Feed/clean actions, composable need decay with conditions |
| [character-builder.md](character-builder.md) | COMPLETE | Avatar creation, appearance state, skin catalog (12 skins, 4 tiers) |
| [space-builder.md](space-builder.md) | COMPLETE | Rooms, room catalog |
| [social-maintenance.md](social-maintenance.md) | COMPLETE | Social interactions (visit/gift/chat), history, vampiric drift effects |
| [game-loop.md](game-loop.md) | COMPLETE | Tick engine, session open, `GameEvent` animation contract |
| [persistence.md](persistence.md) | COMPLETE | Snapshot serialization, `StoreProtocol`, `MemoryStore` |
| [api.md](api.md) | COMPLETE | FastAPI endpoints, `EventBus`, SSE stream, dependency injection |
| [pwa.md](pwa.md) | IN PROGRESS | PWA frontend, CSS animation engine, phone-first UX, install prompts |
| [deploy.md](deploy.md) | ACTIVE | Fly.io, Railway, Cloudflare Tunnel — real-device testing guide |
