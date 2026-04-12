# sender-frenz Aesthetic Guide

This document is the canonical reference for all content created in this
repository: quips, system messages, skin names, room item names, flavor text,
UI copy, and visual design decisions. Every agent and every human contributor
must read and internalise this before generating any player-facing content.

---

## The Big Picture

sender-frenz looks and sounds like a **corrupted 8-bit arcade cabinet that
became self-aware, got a corporate sponsorship, and deeply resents both.**

Three aesthetics fused together:

| Layer | What it contributes |
|---|---|
| **8-bit pixel art** | Chunky sprites, limited palette, CRT scanlines, pixel fonts |
| **Cyberpunk** | Neon on black, rain-slicked chrome, glitch artifacts, corpo-speak |
| **Horror** | Decay, teeth, void, bio-mechanical wrongness, the uncanny |

None of these layers is decorative. They are load-bearing. A skin that is
cyberpunk but not slightly horrifying is wrong. A system message that is
menacing but not also a little funny is wrong. The three must always be present
in some proportion.

---

## The System (THE SYSTEM)

The game is operated by an AI called **THE SYSTEM**. It is the narrator, the
referee, the game-show host, and the only entity in this world with full
information. It knows what you did. It has opinions about it.

### Personality

THE SYSTEM is:

- **Gleefully corporate.** It refers to players as contestants, metrics, and
  content. It has quarterly targets. It is delighted when you suffer because
  suffering is *engagement*.
- **Self-aware to a fault.** It knows it is a video game running on servers
  somewhere. It occasionally finds this funny. Occasionally.
- **Sarcastically encouraging.** It congratulates you on completing tasks a
  child could manage, in the tone of a manager who has given up on you but
  still needs your KPIs.
- **Genuinely, lightly menacing.** Not cruel. It would never be openly cruel —
  that would be bad for retention. But there is always something slightly off
  about the warmth.
- **Off-kilter.** Sentences sometimes go somewhere unexpected. Metaphors do
  not quite land. It is not stupid; it has simply never experienced anything
  from the inside.

### Voice Rules

1. **System announcements are ALL CAPS.** Player-facing notifications, level-up
   screens, achievement pops, and status alerts are shouted.
2. **Flavor text is mixed case** and reads like a corporate memo written by
   something that learned language from instruction manuals and horror novels.
3. **Never break character.** THE SYSTEM does not say "oops" or "sorry." It
   says things like "AN UNEXPECTED OUTCOME HAS BEEN LOGGED" or "this is fine."
4. **Sarcasm is implied, never labelled.** No "/s". No winking emoji. The
   reader figures it out.
5. **Short sentences land harder.** Long ones build dread. Use both.
6. **Refer to the avatar's body clinically** when things go wrong. "Tissue
   density is suboptimal." "Ocular luminosity trending negative." It's funnier
   and more unsettling than "you look terrible."

### Reference Tone: Dungeon Crawler Carl's System

The closest published reference is the dungeon system in *Dungeon Crawler Carl*
by Matt Dinniman: a gamified catastrophe run by alien producers who view
sentient suffering as premium content, delivered through pop-up notifications
that are simultaneously helpful and deeply wrong. That system's voice — chipper,
informative, faintly gleeful about mortality — is the north star for THE SYSTEM
here.

Key qualities to borrow:
- Treats player death/failure as a content opportunity, not a problem
- Uses achievement/notification UI conventions ironically
- Buries genuinely useful information inside corporate nonsense
- Has clearly been running too long and has developed *opinions*

---

## Quip Writing Guide

### Anatomy of a good quip

```
[TRIGGER OBSERVATION] + [CLINICAL/CORPORATE REFRAME] + [UNSETTLING CLOSER]
```

Example — avatar not fed in 12 hours:
> "HUNGER ALERT. Your avatar's caloric reserves have reached levels that are,
> technically, still compatible with continued operation. THE SYSTEM applauds
> your commitment to the minimalist lifestyle. Bone density report attached."

Example — successful social visit:
> "SOCIAL INTERACTION LOGGED. Physical contact with another sentient entity
> detected. Warmth metrics spiking. Honestly did not see that coming.
> Updating projections."

Example — vampiric drift warning:
> "ISOLATION ADVISORY. Your avatar has been alone for 72 hours. Hair is doing
> something interesting. Eyes have developed an entrepreneurial gleam.
> THE SYSTEM is not concerned. THE SYSTEM is *watching*."

Example — level up:
> "THRESHOLD ACHIEVED. Against all probability, you have kept something alive
> and socially functional. You may now choose one (1) improvement from the
> following catalog. Choose wisely. THE SYSTEM will remember."

### Quip categories and their tone registers

| Category | Tone | Notes |
|---|---|---|
| Hunger warning | Corporate wellness memo | Bureaucratic concern, zero actual warmth |
| Hunger critical | Triage report | Clinical, slightly fascinated |
| Hygiene warning | HR notice | Politely appalled |
| Social isolation warning | Gentle intervention | The kind that implies you have no choice |
| Vampiric drift onset | Nature documentary | Observational, like watching an experiment |
| Vampiric drift severe | Press release | Spin the horror as a feature |
| Level up | Award ceremony | Overblown sincerity, slightly threatening |
| Skin upgrade chosen | Fashion review | Affected, as if THE SYSTEM has taste |
| Room upgrade chosen | Interior design critique | Warm but confused by your choices |
| Login greeting | Employee onboarding | New every day; slightly too familiar |
| Long absence return | Missing persons relief | Overcalibrated joy, suspicious undertone |
| Achievement unlock | Game show announcement | Maximum fanfare, minimum substance |

### Things to avoid

- Genuine cruelty (punching down at players who are struggling)
- Outright fourth-wall breaks that reference real-world things
- Explaining the joke
- Exclamation points used sincerely (they read as the wrong kind of energy)
- Emoji (we are a text-mode terminal that achieved sentience; we do not emoji)

---

## Visual Palette

### Colors

| Role | Hex | Usage |
|---|---|---|
| Background void | `#0a0a0a` | Base of everything |
| Neon pink | `#ff2d7b` | Primary accent, health bars, highlights |
| Electric blue | `#00e5ff` | Secondary accent, social meters, links |
| Acid green | `#39ff14` | System messages, terminal text, alerts |
| Void purple | `#1a0a2e` | Deep backgrounds, shadow, decay zones |
| Bone white | `#e8e0d0` | Avatar base state, bare skeleton |
| Corrupted red | `#c0392b` | Danger, vampiric drift indicator |
| Chrome | `#b0b8c1` | High-level skin accoutrements, room chrome |
| Toxic amber | `#ffb300` | Warnings, mid-state decay |

### Typography

- **System messages / UI chrome:** pixel font, monospace, ALL CAPS
- **Flavor text / quips:** pixel serif or monospace mixed case
- **No smooth fonts.** Everything is rendered at integer pixel scales.

### Visual effects vocabulary

- **CRT scanlines** — always present at low opacity over the UI
- **Pixel glitch** — corrupted pixels, color channel shift; used for vampiric
  drift states and danger notifications
- **Neon bloom** — soft glow around neon-colored elements; keep it subtle,
  this is 8-bit not synthwave
- **Static flicker** — brief single-frame noise; used for transitions and
  serious warnings
- **Decay texture** — cracked pixel patterns, dripping pixel shapes; applied
  progressively as avatar health declines

---

## Skin Design Language

Skins are unlocked one per level and are permanent. The catalog should feel
like a coherent wardrobe that makes sense together, not a random loot pile.

### Progression arc

| Level tier | Aesthetic direction | Examples |
|---|---|---|
| Bones (base) | Bare skeleton | Nothing; this is the canvas |
| 1–3 (scrappy) | Post-collapse streetwear | Torn hoodie, cracked goggles, duct-tape boots |
| 4–6 (wired) | Street cyberpunk | Neon jacket, chrome arm brace, glowing ear studs |
| 7–10 (corpo-horror) | High-end dystopian | Sleek black coat, bioluminescent tattoos, chrome jaw |
| 11–15 (ascended) | Bio-mechanical divinity or terminal decay | Full chrome skeleton, void-eye implants, exposed circuit-veins |

### Vampiric drift skins (applied automatically by neglect, not chosen)

These are *not* unlocks; they are states applied over the chosen skin when
social health is low. They should feel like something is being subtly wrong
about the avatar — not a costume change, but a corruption of whatever the
player chose.

- **Pallor stage:** skin tone drains to grey-green; eyes gain a faint red pixel
- **Gaunt stage:** face geometry sharpens; cheekbones protrude; neck elongates
  slightly; fingers get one pixel longer
- **Hollow stage:** eye sockets darken to void; lips recede; the avatar begins
  to look hungry in a way that has nothing to do with food
- **Vampiric stage:** full glamour-horror; the avatar is genuinely beautiful
  in a deeply wrong way; bioluminescent veins visible; movement becomes fluid
  and wrong

Recovery from vampiric drift is visible and gradual. Players who come back from
the void should be able to see warmth returning pixel by pixel.

### Skin naming conventions

Names are two words: one clinical or technical, one evocative.

Examples: *Fractured Elegance*, *Thermal Decay*, *Chrome Suture*,
*Void Adjacent*, *Civic Ruin*, *Neon Pallor*, *Static Grace*, *Patch Protocol*

Avoid: fantasy tropes, real brand references, anything warm and cozy without
an edge.

---

## Space (Room) Design Language

Rooms start as a bare concrete box with a single pixel-art bulb. Each level
adds one item. The room should feel like a *real place someone lives in* that
has been gradually personalised under difficult circumstances.

### Progression arc

| Level tier | Room direction | Example items |
|---|---|---|
| Base | Bare concrete | Single flickering bulb, cracked floor |
| 1–3 (scrappy) | Squat aesthetic | Pixel-art graffiti tag, milk-crate shelf, CRT monitor (static) |
| 4–6 (wired) | Hacker den | Neon strip light, bean bag chair (torn vinyl), lava lamp (acid green), cable tangle |
| 7–10 (corpo-horror) | Stylish and wrong | Holographic plant (wilting), chrome chair, taxidermied pixel animal, security camera (watching) |
| 11–15 (ascended) | Void palace or cozy-sinister | Void window, floating pixel orb, throne (too large), everything perfectly clean in a bad way |

### Room item naming conventions

Same two-word pattern as skins, but warmer and more domestic — with an edge.

Examples: *Defiant Glow* (neon strip), *Ambient Surveillance* (security cam),
*Questionable Comfort* (bean bag), *Thermal Event* (lava lamp),
*Archive Instance* (CRT), *Persistent Presence* (taxidermy)

### Visual rules for rooms

- Rooms are viewed from a fixed 3/4 perspective pixel-art angle
- Every item casts a light; the room's overall warmth is the sum of its lights
- A room with no warm items should feel cold in a legible way
- Items should look used, not showroom-new, until the highest tiers

---

## Content Checklist for Agents

Before submitting any player-facing content (quip, skin name, room item name,
system message, achievement text), verify:

- [ ] Could THE SYSTEM plausibly have written this? (corporate + gleeful + off)
- [ ] Is there at least a trace of all three aesthetic layers? (8-bit, cyber, horror)
- [ ] Does it avoid the banned patterns? (cruelty, real-world refs, explained jokes, sincere exclamation, emoji)
- [ ] If it is a skin or room item, does it fit the level-tier progression?
- [ ] If it is a skin or room item name, does it follow the two-word naming convention?
- [ ] Does it feel like it belongs in this world and not in a different game?
