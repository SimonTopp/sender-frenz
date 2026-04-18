# Plan: PWA Frontend — Phase 9

**Status:** PLANNED
**Written:** April 2026

---

## Goal

Build the first playable client: a Progressive Web App that talks to the Phase
8 API, renders the avatar, plays animations on game events, and works as a
phone-first experience.

**Phone-first constraint:** the entire development and testing workflow must
work from a phone.  No laptop required.  This shapes every tech decision.

**Social constraint:** sender-frenz is multiplayer at its core — two avatars
interacting is the long-term vision.  Nothing in Phase 9 should block that.
Social views, peer-to-peer interaction flows, and avatar discovery are Phase N
concerns, but the navigation and component structure must accommodate them
without a major refactor.

---

## Tech Stack

### No build step

The PWA is plain HTML + CSS + ES modules.  No bundler.  No npm.  No build
command.

Rationale:
- The primary development workflow (see below) is Claude for Web — changes
  are described in conversation and applied to files.  A bundler would require
  a running build step that's invisible to this workflow.
- ES modules (`<script type="module">`) work in every browser the app targets.
- The app is a single-player tamagotchi (with multiplayer on the horizon).
  Code volume stays manageable as plain files.

If a build step is ever needed (TypeScript, tree-shaking), Vite can be added
later.  The file layout below is Vite-compatible; the migration is a
`vite.config.js` away.

### Files

```
web/
  index.html          shell: loads manifest, CSS, and app.js
  manifest.json       PWA metadata (name, icons, display: standalone)
  sw.js               service worker
  style.css           layout + visual state classes + keyframe animations
  app.js              entry: boot, session open, SSE listener, routing
  avatar.js           renders SessionResponse / ActionResponse into DOM
  actions.js          POST /action/{kind} + optimistic UI
  level_up.js         upgrade picker flow

tests/pwa/
  conftest.py         live server fixture + Pixel 7 browser context
  test_session.py     session open → correct DOM state
  test_actions.py     all five actions end-to-end
  test_level_up.py    upgrade picker flow
  test_sse.py         SSE event received → correct CSS class applied
  test_errors.py      missing header, unknown avatar, API unreachable

.github/
  workflows/
    lighthouse.yml    PWA compliance check on every PR
```

`pytest-playwright` is added to the dev dependency group.  No separate JS
test toolchain is needed — everything runs through `uv run pytest`.

---

## Serving the PWA

FastAPI serves the `web/` directory as static files mounted at `/`.  No
separate static server is needed:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="web", html=True), name="static")
```

This means `uvicorn sender_frenz.api:app` serves both API and frontend from
one process.  The phone opens `http://<server-ip>:8000` and gets the app.

**Hosting:** the FastAPI + static approach works for any platform that runs a
Python process.  Hosting options (Fly.io, Railway, Render, etc.) and production
infrastructure are a future discussion — Phase 9 scope is development and the
runnable PWA, not production deployment.

---

## Phone Development Workflow

### Primary workflow: Claude for Web

The primary development method is conversation-driven: describe the change to
Claude at claude.ai, Claude implements it.  No local terminal, no mobile code
editor required.

This means:
- Claude proposes file changes in-conversation; they land in the repo via
  the Claude Code session.
- The user reviews on their phone via GitHub's web interface or by loading
  the running app.
- Claude runs `uv run pytest`, `uv run ruff check .`, and `uv run mypy .`
  to verify backend changes.  Frontend changes are validated by loading the
  app in a phone browser.

If this workflow ever changes (e.g., direct Termux/iSH terminal access), update
this section.

### Accessing the server from the phone

The FastAPI dev server binds to `0.0.0.0:8000`.  The phone connects via the
server's LAN IP (`http://192.168.x.x:8000`) or a tunnel.

**HTTPS caveat:** service workers and PWA install prompts require HTTPS or
`localhost`.  For a remote server, use a tunnel:

1. **Cloudflare Tunnel (recommended):** `cloudflared tunnel --url http://localhost:8000`
   gives a stable `https://*.trycloudflare.com` URL with a valid TLS cert.
   Free, no account required for quick tunnels.
2. **ngrok:** `ngrok http 8000`.  Free tier resets the URL on restart.

### Debugging on the phone

Add Eruda behind a `?debug=1` query-param guard:

```html
<script>
  if (location.search.includes("debug=1")) {
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/eruda";
    s.onload = () => eruda.init();
    document.head.appendChild(s);
  }
</script>
```

Eruda provides a mobile-browser console, network inspector, and element tree
without leaving the app.  The guard ensures it never ships to production users.

---

## Screens and Navigation

Single-page app with named views toggled via CSS or DOM swaps.  The navigation
structure must accommodate future social/multiplayer views without a major
refactor — use a tab-bar or slot-based layout with room for a fourth tab.

### Phase 9 views

**1. Main view** — everything reachable from one scroll:

```
[ avatar display — skin slug + vampiric stage as CSS classes ]
[ room name + description line ]
[ need meters: hunger bar + hygiene bar ]
[ social bar + stage label ]
[ action buttons: FEED  CLEAN  VISIT  GIFT  CHAT ]
[ level-up badge (hidden until level_up_available) ]
[ quip line (last quip or login quip) ]
```

**2. Level-up picker** — shown when the level-up badge is tapped:

```
[ skin option cards — 2-3 cards, slug + name + description ]
[ room option cards — 2-3 cards ]
[ CONFIRM button ]
```

**3. Loading / error state** — full-screen spinner on first session open;
full-screen error + RETRY if the API is unreachable.

### Future social view (Phase N placeholder)

The navigation shell should reserve a slot for a social/multiplayer view that
will handle avatar discovery, peer interaction (including NFC tap and QR-code
flows — see Social Actions below), and viewing another avatar's state.  Phase 9
does not implement this view, but the layout must not make it awkward to add.

---

## Avatar Display

The avatar is rendered as **layered CSS classes**, not static images.  The
layered `div` structure is the intentional migration path to composable
per-slug animations — each layer is an independent animation target.

```html
<div class="avatar"
     data-skin="torn-canvas"
     data-stage="dormant"
     data-hunger="hungry"
     data-hygiene="clean">
  <div class="avatar__body"></div>
  <div class="avatar__skin-layer"></div>
  <div class="avatar__room-layer"></div>
  <div class="avatar__status-fx"></div>
</div>
```

**End-goal architecture:** every skin slug and room slug maps to its own
composable looping animation.  Animations stack — the skin layer plays its
idle loop independently of the body layer and the room layer.  When art assets
arrive, replacing a CSS rule with an animated sprite or Lottie component
requires only touching that layer's CSS/JS; the data-attribute contract and
the layer structure are unchanged.

```css
/* v1: pure CSS visual */
.avatar[data-skin="neon-pallor"] .avatar__skin-layer { box-shadow: 0 0 8px cyan; }

/* future: per-slug animated asset, same selector */
.avatar[data-skin="neon-pallor"] .avatar__skin-layer {
  background-image: url("/assets/skins/neon-pallor.gif");
  animation: neon-pallor-idle 2s steps(4) infinite;
}
```

`data-*` attributes map directly from `AppearanceResponse`:

| Attribute | Source field | Values |
|---|---|---|
| `data-skin` | `skin_slug` | catalog slug or `null` |
| `data-stage` | `vampiric_stage` | `dormant`, `pale`, `gaunt`, `hollow`, `vampiric` |
| `data-hunger` | `hunger_visual` | `nourished`, `hungry`, `starved` |
| `data-hygiene` | `hygiene_visual` | `clean`, `unkempt`, `grimy` |

---

## Animations and the GameEvent Contract

The `SessionResponse.events` list is the animation contract.  On session open,
replay events in order.  On SSE message, process the incoming event.

```js
// animations.js
const ANIMATION_MAP = {
  hunger_warning:     () => triggerClass(avatar, "anim--hunger-warn", 1200),
  hunger_critical:    () => triggerClass(avatar, "anim--hunger-crit", 800),
  hygiene_warning:    () => triggerClass(avatar, "anim--hygiene-warn", 1200),
  hygiene_critical:   () => triggerClass(avatar, "anim--hygiene-crit", 800),
  social_warning:     () => triggerClass(avatar, "anim--social-warn", 1500),
  social_critical:    () => triggerClass(avatar, "anim--social-crit", 1500),
  vampiric_advance:   () => triggerStageTransition("advance"),
  vampiric_retreat:   () => triggerStageTransition("retreat"),
  level_up_ready:     () => showLevelUpBadge(),
};

function triggerClass(el, cls, durationMs) {
  el.classList.add(cls);
  setTimeout(() => el.classList.remove(cls), durationMs);
}
```

`triggerClass` is the entire animation engine for v1.  CSS keyframes do the
visual work; JS applies and removes the class.  Stage transitions update the
persistent `data-stage` attribute after the animation completes.

### Animation CSS sketch

```css
@keyframes hunger-warn {
  0%   { transform: translateY(0); }
  25%  { transform: translateY(-4px); }
  75%  { transform: translateY(2px); }
  100% { transform: translateY(0); }
}
.anim--hunger-warn .avatar__body {
  animation: hunger-warn 0.6s ease-in-out 2;
}

@keyframes starve-shake {
  0%, 100% { transform: translateX(0); }
  20%       { transform: translateX(-6px); }
  40%       { transform: translateX(6px); }
  60%       { transform: translateX(-4px); }
  80%       { transform: translateX(4px); }
}
.anim--hunger-crit .avatar__body {
  animation: starve-shake 0.4s ease-in-out;
}
```

---

## SSE Connection

```js
function connectSSE(avatarId) {
  const source = new EventSource(`/events/${avatarId}`);
  source.onmessage = (e) => {
    const event = JSON.parse(e.data);
    const handler = ANIMATION_MAP[event.kind];
    if (handler) handler();
  };
  source.onerror = () => {
    source.close();
    setTimeout(() => connectSSE(avatarId), 5000);
  };
}
```

Reconnect on disconnect with exponential back-off (cap at 30s).  iOS Safari
kills SSE connections in the background — the reconnect loop handles this.

---

## Action Flow

Actions are optimistic: button disables immediately, API call fires, response
updates the display.

```
tap FEED
  → button.disabled = true
  → POST /action/feed
  → on 200: update need meters from ActionResponse + display quip
  → on error: re-enable button + display error quip
```

The `quip` field from `ActionResponse` replaces the current quip line.
THE SYSTEM's voice is the primary feedback mechanism.

Haptic feedback via the Vibration API on action tap (where supported):

```js
if ("vibrate" in navigator) navigator.vibrate(30);
```

### Social actions: v1 and future path

**Phase 9 (v1):** VISIT, GIFT, and CHAT call `POST /action/{kind}` for the
player's own avatar, exactly like FEED and CLEAN.  No peer involvement.
This gets social mechanics into players' hands quickly.

**Future:** social actions will involve a second avatar.  The long-term
interaction model includes:
- **NFC tap** — two phones tap to trigger a mutual social event (Web NFC API;
  currently Android Chrome only; iOS requires a native wrapper).
- **QR code** — one avatar displays a QR code; the other scans it to initiate
  the interaction.  Works cross-platform in the browser today.
- **Avatar discovery** — find nearby or recently-interacted avatars via the API.

The Phase 9 UI must not make these flows awkward to add.  Concretely:
- Social action buttons should be visually grouped and separable from
  maintenance buttons (FEED, CLEAN) in the layout.
- The `POST /action/{kind}` endpoint already accepts an `Avatar-Id` header;
  extending it to accept a `Target-Avatar-Id` header is a small API change
  that does not require restructuring the frontend.
- Do not hardcode "solo action" assumptions into component logic.

---

## Phone-First UX Requirements

Every screen must satisfy all of these.

- **Touch targets:** minimum 48 × 48 CSS pixels.  Action buttons ≥ 56px tall.
  Level-up cards are full-width.
- **Thumb zone:** primary actions (FEED, CLEAN) at the bottom of the viewport.
  Secondary actions above those.  Future social tab reachable from the same
  thumb position.
- **No hover states:** every interactive element has a `:active` state.
  No `:hover`-only feedback.
- **Font size:** body text ≥ 16px to prevent iOS automatic zoom on tap.
- **Viewport meta:** `<meta name="viewport" content="width=device-width,
  initial-scale=1, viewport-fit=cover">`.
- **Safe area insets:** bottom bar padded with `env(safe-area-inset-bottom)`.
- **Portrait-primary:** design and test in portrait.
- **No 300ms tap delay:** `touch-action: manipulation` on interactive elements.

---

## PWA Manifest and Install

```json
{
  "name": "sender frenz",
  "short_name": "frenz",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0a0a",
  "theme_color": "#0a0a0a",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

Icons can be placeholder colored squares for v1.

**iOS install:** show an in-app banner ("tap Share → Add to Home Screen") on
second visit if not already installed.  Detect with
`window.matchMedia("(display-mode: standalone)")`.

**Android install:** listen for `beforeinstallprompt`; show a button that
calls `prompt()`.

---

## Service Worker

- **Shell assets** (`index.html`, `style.css`, `app.js`, `manifest.json`,
  icons): cache-first with a versioned cache name.
- **API requests**: network-only (game state must always be fresh).
- **SSE stream**: bypass service worker entirely.

On activation, delete old cache versions.

---

## Push Notifications

Deferred to Phase 10.  Web Push requires HTTPS, VAPID keys, a per-avatar
subscription endpoint (new persistence concern), and notification triggers in
the game loop.  The SSE stream covers real-time updates while the app is open.
Phase 10 (native shell) handles background notifications via APNs / FCM.

---

## Test Strategy

Two tiers: automated Playwright for regression coverage, manual phone for
things automation can't verify (install prompts, real touch feel, iOS quirks).

### Automated: Playwright

`pytest-playwright` runs headless Chromium in a **Pixel 7 device profile**
(412 × 915 viewport, `is_mobile=True`, `has_touch=True`, 2.625× DPR).  The
same `uv run pytest` command that runs backend tests runs these.  A live
FastAPI server is started per test session via a `conftest.py` fixture.

**What Playwright covers:**

| Suite | Scenarios |
|---|---|
| `test_session.py` | Session open → correct meter values, quips, avatar `data-*` attributes set |
| `test_actions.py` | Each of the five actions → DOM updates, quip changes, button re-enables |
| `test_level_up.py` | Badge appears when eligible; picker shows correct options; confirm applies upgrade |
| `test_sse.py` | Publish event via `EventBus` directly → correct CSS class added to avatar element |
| `test_errors.py` | Missing `Avatar-Id` header → error view; API unreachable → error + retry button |

**What Playwright does NOT cover (manual only):**

- PWA install prompt (requires HTTPS + native browser UI)
- iOS Safari-specific behaviour (safe-area insets, background SSE kill/reconnect)
- Actual touch feel, thumb reachability, and scroll momentum
- Real network latency and LTE load time

### Lighthouse CI

A GitHub Actions workflow starts the FastAPI server and runs
`@lhci/cli autorun` on every push and PR.  Fails if the PWA score drops below
90.

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [push, pull_request]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install uv && uv sync --group dev
      - name: Start server
        run: uvicorn sender_frenz.api:app --host 0.0.0.0 --port 8000 &
      - run: sleep 2
      - run: npx --yes @lhci/cli autorun --upload.target=temporary-public-storage
```

### Manual checklist (real phone, final gate before COMPLETE)

- [ ] Opening the URL loads the main view within 2s on LTE
- [ ] Session open displays avatar state and quips
- [ ] Each action updates the display and shows a quip
- [ ] Level-up badge appears, picker works, upgrade applies
- [ ] SSE connection visible in Eruda network tab; animation triggers on event
- [ ] "Add to Home Screen" prompt fires on Android
- [ ] iOS install banner shows on second visit
- [ ] Installed PWA launches in standalone mode (no browser chrome)
- [ ] Back-swipe / gesture navigation does not break app state
- [ ] Rotating to landscape does not break layout
- [ ] Action buttons reachable with one thumb; no accidental adjacent taps
- [ ] Social action buttons visually distinct from maintenance buttons
- [ ] App reconnects SSE after returning from background (iOS Safari kills SSE)
- [ ] `?debug=1` loads Eruda; production URL does not

---

## Definition of Done

- [ ] `web/` directory committed and served by FastAPI static mount
- [ ] All three views implemented (main, level-up picker, loading/error)
- [ ] All five actions wired end-to-end
- [ ] All nine `GameEvent` kinds trigger a visible animation or UI change
- [ ] Avatar display uses layered div structure (body, skin-layer, room-layer, status-fx)
- [ ] Social action buttons visually grouped, layout accommodates future peer-interaction flow
- [ ] `uv run pytest tests/pwa/` passes headless (Pixel 7 profile)
- [ ] `.github/workflows/lighthouse.yml` present; PWA score ≥ 90
- [ ] Service worker caches shell assets; API calls bypass cache
- [ ] Manual checklist above completed on real phone
- [ ] Eruda guard in place (`?debug=1` only)
- [ ] No console errors in production mode
- [ ] `docs/pwa.md` status updated to COMPLETE
