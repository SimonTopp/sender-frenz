# Deployment Guide

**Status:** ACTIVE
**Written:** April 2026

---

## Overview

sender-frenz runs as a single `uvicorn` process serving both the FastAPI
backend and the `web/` static frontend.  Any platform that can run a Python
process and expose a port over HTTPS will work.

Current state: `MemoryStore` — avatar state lives in-process and resets on
restart.  This is fine for testing; a database-backed store is a future phase.

---

## Option 1: Fly.io (recommended)

Free hobby tier, HTTPS out of the box, auto-sleep on inactivity.

### First deploy

```bash
# Install flyctl (one-time)
curl -L https://fly.io/install.sh | sh

# Authenticate
fly auth login

# Launch — accepts fly.toml from the repo; pick the nearest region
fly launch --no-deploy

# Deploy
fly deploy
```

The app will be live at `https://sender-frenz.fly.dev` (or whatever name you
picked at launch).  Open that URL on your phone.

### Subsequent deploys

```bash
fly deploy
```

Or connect the GitHub repo to Fly.io for auto-deploy on push to `main` via
the Fly.io dashboard → Continuous Deployment.

### Scaling / cost

The default `fly.toml` uses `auto_stop_machines = true` — the machine sleeps
when idle and wakes on the next request (~2s cold start).  Zero cost when not
in use.  Upgrade to `min_machines_running = 1` for always-on.

---

## Option 2: Railway

Connects to GitHub; auto-deploys on push.  Uses the `Procfile`.

1. Create a new project at railway.app
2. Connect the `simontopp/sender-frenz` repository
3. Railway detects `uv.lock` + `Procfile` and deploys automatically
4. The public URL appears in the Railway dashboard

No CLI required — entirely web UI.

---

## Option 3: Cloudflare Tunnel (dev/testing only)

Exposes a locally-running server via HTTPS without deployment.  Useful for a
quick phone test without committing to a hosting platform.

```bash
# Install cloudflared (one-time)
# macOS: brew install cloudflare/cloudflare/cloudflared
# Linux: https://pkg.cloudflare.com/index.html

# Start the tunnel (run alongside uvicorn)
uvicorn sender_frenz.api:app --host 127.0.0.1 --port 8000 &
cloudflared tunnel --url http://localhost:8000
```

`cloudflared` prints a `https://*.trycloudflare.com` URL.  Open it on your
phone.  No account required.  URL changes on every restart.

---

## Real-device testing checklist

Once the app is live at an HTTPS URL, work through this checklist on a real
phone:

- [ ] Opening the URL loads the main view within 2s on LTE
- [ ] Session open displays avatar state and quips
- [ ] Each of the five actions updates the display and shows a quip
- [ ] Level-up badge appears when eligible; picker works; upgrade applies
- [ ] SSE connection visible in Eruda network tab (`?debug=1`)
- [ ] Avatar state updates automatically (background tick fires every 30s)
- [ ] **Android:** "Add to home screen" banner appears after first visit;
      Install prompt fires; installed app launches in standalone mode
- [ ] **iOS:** "Tap Share → Add to Home Screen" banner appears on second visit;
      installed app launches in standalone mode (no browser chrome)
- [ ] Back-swipe / gesture navigation does not break app state
- [ ] Rotating to landscape does not break layout
- [ ] Action buttons reachable with one thumb
- [ ] App reconnects SSE after returning from background (iOS Safari kills SSE)
- [ ] `?debug=1` loads Eruda; production URL does not load Eruda
