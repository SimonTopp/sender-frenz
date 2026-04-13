"""Skin upgrade catalog for character_builder.

This module is the authoritative source of skin :class:`UpgradeOption` instances.
It is consumed by :func:`sender_frenz.common.levels.skin_options_for_level` and
:func:`sender_frenz.common.levels.apply_level_up` — pass :data:`SKIN_CATALOG` as
the ``skin_catalog`` argument to those functions.

The catalog follows the level-tier progression described in ``docs/aesthetic.md``:

- **Tier 1 (levels 1-3):** Post-collapse streetwear -- scavenged, stitched, and
  held together with optimism and duct tape.
- **Tier 2 (levels 4-6):** Street cyberpunk -- wired fabric, neon thread, and
  materials that react poorly to proximity to certain frequencies.
- **Tier 3 (levels 7-10):** Corpo-horror -- high-end dystopian; wealth expressed
  as visible damage, surgical-grade closures, and fabrics that eat light.
- **Tier 4 (levels 11+):** Ascended -- bio-mechanical divinity or terminal decay;
  the boundary between garment and organism is advisory at this tier.

All names follow the two-word convention from ``docs/aesthetic.md``.
"""

from __future__ import annotations

from sender_frenz.common.levels import UpgradeOption

# ---------------------------------------------------------------------------
# Tier boundaries
# ---------------------------------------------------------------------------

_TIER_1_MIN_LEVEL: int = 1
"""Minimum avatar level for tier-1 skins (post-collapse streetwear)."""

_TIER_2_MIN_LEVEL: int = 4
"""Minimum avatar level for tier-2 skins (street cyberpunk)."""

_TIER_3_MIN_LEVEL: int = 7
"""Minimum avatar level for tier-3 skins (corpo-horror)."""

_TIER_4_MIN_LEVEL: int = 11
"""Minimum avatar level for tier-4 skins (ascended / bio-mechanical)."""

# ---------------------------------------------------------------------------
# Skin catalog entries
# ---------------------------------------------------------------------------

# Tier 1 — post-collapse streetwear

_TORN_CANVAS = UpgradeOption(
    slug="torn-canvas",
    name="Torn Canvas",
    tier=_TIER_1_MIN_LEVEL,
    description=(
        "Scavenged sailcloth, bleached and re-bleached until the original colour"
        " is a matter of speculation. The seams are doing their best. THE SYSTEM"
        " commends their effort."
    ),
)

_PATCH_PROTOCOL = UpgradeOption(
    slug="patch-protocol",
    name="Patch Protocol",
    tier=_TIER_1_MIN_LEVEL,
    description=(
        "Duct tape, cable ties, and one (1) functioning zip. Someone was optimistic"
        " about the structural integrity. That optimism has been partially vindicated."
        " Partially."
    ),
)

_CIVIC_RUIN = UpgradeOption(
    slug="civic-ruin",
    name="Civic Ruin",
    tier=_TIER_1_MIN_LEVEL,
    description=(
        "Salvage-grade textile with a collar that has chosen its own direction."
        " It survives because nothing else does. THE SYSTEM finds this relatable."
    ),
)

# Tier 2 — street cyberpunk

_NEON_PALLOR = UpgradeOption(
    slug="neon-pallor",
    name="Neon Pallor",
    tier=_TIER_2_MIN_LEVEL,
    description=(
        "A jacket that glows in the wrong frequencies. Light sources in its"
        " vicinity report a mild disagreement. Wear it indoors at your own"
        " electromagnetic risk."
    ),
)

_STATIC_GRACE = UpgradeOption(
    slug="static-grace",
    name="Static Grace",
    tier=_TIER_2_MIN_LEVEL,
    description=(
        "Chrome-threaded mesh that produces a faint electrical complaint when"
        " the wearer moves. Nearby devices describe the experience as"
        " unprofessional. THE SYSTEM disagrees."
    ),
)

_THERMAL_DECAY = UpgradeOption(
    slug="thermal-decay",
    name="Thermal Decay",
    tier=_TIER_2_MIN_LEVEL,
    description=(
        "Heat-reactive polymer weave. Colour shifts with body temperature and"
        " emotional state, in that order. Currently reading amber. THE SYSTEM"
        " notes this without comment."
    ),
)

# Tier 3 — corpo-horror

_CHROME_SUTURE = UpgradeOption(
    slug="chrome-suture",
    name="Chrome Suture",
    tier=_TIER_3_MIN_LEVEL,
    description=(
        "Surgical-grade closures visible through a semi-transparent outer layer."
        " THE SYSTEM categorises this as decorative. The closures are not holding"
        " anything closed. Allegedly."
    ),
)

_VOID_ADJACENT = UpgradeOption(
    slug="void-adjacent",
    name="Void Adjacent",
    tier=_TIER_3_MIN_LEVEL,
    description=(
        "Bespoke matte-black coat that absorbs light in a manner that has attracted"
        " regulatory interest. Warm. Unnervingly warm. THE SYSTEM has filed the"
        " relevant paperwork."
    ),
)

_FRACTURED_ELEGANCE = UpgradeOption(
    slug="fractured-elegance",
    name="Fractured Elegance",
    tier=_TIER_3_MIN_LEVEL,
    description=(
        "High-gloss fibre disrupted by deliberate micro-fractures. Wealth expressed"
        " as visible damage. The cracks are load-bearing. Do not ask what they are"
        " bearing."
    ),
)

# Tier 4 — ascended / bio-mechanical

_CIRCUIT_VEIN = UpgradeOption(
    slug="circuit-vein",
    name="Circuit Vein",
    tier=_TIER_4_MIN_LEVEL,
    description=(
        "Subcutaneous bioluminescent threading visible through all subsequent"
        " layers. THE SYSTEM classifies the light source as internal. The"
        " classification is accurate in ways that should concern you."
    ),
)

_NULL_SHROUD = UpgradeOption(
    slug="null-shroud",
    name="Null Shroud",
    tier=_TIER_4_MIN_LEVEL,
    description=(
        "A garment that achieves full opacity only at certain light angles."
        " THE SYSTEM cannot fully categorise it. THE SYSTEM has tried. THE SYSTEM"
        " has filed an incident report and moved on."
    ),
)

_SIGNAL_FLESH = UpgradeOption(
    slug="signal-flesh",
    name="Signal Flesh",
    tier=_TIER_4_MIN_LEVEL,
    description=(
        "Terminal-stage integration of organic and synthetic substrate."
        " At this tier the distinction is advisory. THE SYSTEM congratulates"
        " you on your commitment to the process."
    ),
)

# ---------------------------------------------------------------------------
# Public catalog
# ---------------------------------------------------------------------------

SKIN_CATALOG: tuple[UpgradeOption, ...] = (
    # Tier 1
    _TORN_CANVAS,
    _PATCH_PROTOCOL,
    _CIVIC_RUIN,
    # Tier 2
    _NEON_PALLOR,
    _STATIC_GRACE,
    _THERMAL_DECAY,
    # Tier 3
    _CHROME_SUTURE,
    _VOID_ADJACENT,
    _FRACTURED_ELEGANCE,
    # Tier 4
    _CIRCUIT_VEIN,
    _NULL_SHROUD,
    _SIGNAL_FLESH,
)
"""All skin upgrades, ordered by tier then slug.

Pass this to :func:`sender_frenz.common.levels.skin_options_for_level` or
:func:`sender_frenz.common.levels.apply_level_up` as the ``skin_catalog``
argument.
"""


# ---------------------------------------------------------------------------
# Convenience query
# ---------------------------------------------------------------------------


def skins_for_level(level: int) -> tuple[UpgradeOption, ...]:
    """Return all skins whose tier is at or below *level*.

    This is a catalog-side convenience function that does **not** filter
    already-applied slugs.  For the full level-up flow (which also excludes
    previously applied skins), use
    :func:`sender_frenz.common.levels.skin_options_for_level` with the avatar.

    Args:
        level: The avatar's current level.  Values below 1 return an empty
            tuple because no skin requires level 0 or below.

    Returns:
        A tuple of :class:`~sender_frenz.common.levels.UpgradeOption` instances
        ordered by tier then by their position in :data:`SKIN_CATALOG`.
    """
    return tuple(opt for opt in SKIN_CATALOG if opt.tier <= level)
