"""Room upgrade catalog for space_builder.

This module is the authoritative source of room :class:`UpgradeOption`
instances.  It is consumed by :func:`sender_frenz.common.levels.room_options_for_level`
and :func:`sender_frenz.common.levels.apply_level_up` -- pass :data:`ROOM_CATALOG`
as the ``room_catalog`` argument to those functions.

The catalog follows the level-tier progression described in ``docs/aesthetic.md``:

- **Tier 1 (levels 1-3):** Squat aesthetic -- scavenged furnishings, cracked
  surfaces, and items that work only technically speaking.
- **Tier 2 (levels 4-6):** Hacker den -- neon accents, secondhand tech, and
  furniture that has been through at least one relocation under duress.
- **Tier 3 (levels 7-10):** Stylish and wrong -- high-end pieces that are
  subtly, deeply incorrect in ways that resist articulation.
- **Tier 4 (levels 11+):** Void palace / cozy-sinister -- items that exist
  primarily as concepts; the room is doing something the walls were not
  designed for.

All names follow the two-word convention from ``docs/aesthetic.md``.
Tier boundary constants mirror those in ``character_builder.catalog``; they are
duplicated here rather than imported to respect the no-cross-module-imports rule.
"""

from __future__ import annotations

from sender_frenz.common.levels import UpgradeOption

# ---------------------------------------------------------------------------
# Tier boundaries
# (Mirror character_builder.catalog -- see module docstring.)
# ---------------------------------------------------------------------------

_TIER_1_MIN_LEVEL: int = 1
"""Minimum avatar level for tier-1 room items (squat aesthetic)."""

_TIER_2_MIN_LEVEL: int = 4
"""Minimum avatar level for tier-2 room items (hacker den)."""

_TIER_3_MIN_LEVEL: int = 7
"""Minimum avatar level for tier-3 room items (stylish and wrong)."""

_TIER_4_MIN_LEVEL: int = 11
"""Minimum avatar level for tier-4 room items (void palace / cozy-sinister)."""

# ---------------------------------------------------------------------------
# Catalog entries
# ---------------------------------------------------------------------------

# Tier 1 -- squat aesthetic

_ARCHIVE_INSTANCE = UpgradeOption(
    slug="archive-instance",
    name="Archive Instance",
    tier=_TIER_1_MIN_LEVEL,
    description=(
        "A CRT monitor displaying static. It has been displaying static for"
        " longer than anyone can confirm. THE SYSTEM considers it a legacy"
        " system. THE SYSTEM respects legacy systems."
    ),
)

_CIVIC_GRAFT = UpgradeOption(
    slug="civic-graft",
    name="Civic Graft",
    tier=_TIER_1_MIN_LEVEL,
    description=(
        "Pixel-art graffiti tag, origin unknown, applied directly to the"
        " wall. Removal has been attempted. The wall is winning."
        " THE SYSTEM has logged this as personalisation."
    ),
)

_SALVAGE_SHELF = UpgradeOption(
    slug="salvage-shelf",
    name="Salvage Shelf",
    tier=_TIER_1_MIN_LEVEL,
    description=(
        "Milk crates arranged into a shelving unit via optimism and structural"
        " ambiguity. Load-bearing in the emotional sense. THE SYSTEM"
        " notes the contents with interest."
    ),
)

# Tier 2 -- hacker den

_DEFIANT_GLOW = UpgradeOption(
    slug="defiant-glow",
    name="Defiant Glow",
    tier=_TIER_2_MIN_LEVEL,
    description=(
        "Neon strip light in a frequency that should not be available to"
        " residential tenants. It hums at a pitch that is technically"
        " inaudible. THE SYSTEM recommends not thinking about this."
    ),
)

_QUESTIONABLE_COMFORT = UpgradeOption(
    slug="questionable-comfort",
    name="Questionable Comfort",
    tier=_TIER_2_MIN_LEVEL,
    description=(
        "Bean bag chair, torn vinyl, filled with something that shifts"
        " in a way pellets do not. Supports the body with suspicious"
        " thoroughness. THE SYSTEM endorses its continued use."
    ),
)

_THERMAL_EVENT = UpgradeOption(
    slug="thermal-event",
    name="Thermal Event",
    tier=_TIER_2_MIN_LEVEL,
    description=(
        "Lava lamp, acid green, operating outside its rated temperature"
        " range. The fluid has developed a pattern. THE SYSTEM is"
        " documenting the pattern. For science."
    ),
)

# Tier 3 -- stylish and wrong

_AMBIENT_SURVEILLANCE = UpgradeOption(
    slug="ambient-surveillance",
    name="Ambient Surveillance",
    tier=_TIER_3_MIN_LEVEL,
    description=(
        "Security camera, corner-mounted, tracking. The feed goes somewhere."
        " THE SYSTEM declines to specify where. This is a premium feature."
        " THE SYSTEM thanks you for your continued participation."
    ),
)

_PERSISTENT_PRESENCE = UpgradeOption(
    slug="persistent-presence",
    name="Persistent Presence",
    tier=_TIER_3_MIN_LEVEL,
    description=(
        "Taxidermied pixel animal, species unconfirmed, eyes reflecting"
        " light from a source that is not in the room. It has been here"
        " longer than the room. THE SYSTEM does not question this."
    ),
)

_WILTING_SIGNAL = UpgradeOption(
    slug="wilting-signal",
    name="Wilting Signal",
    tier=_TIER_3_MIN_LEVEL,
    description=(
        "Holographic plant, perpetually mid-droop, broadcasting on a"
        " frequency adjacent to longing. The leaves are technically"
        " there. THE SYSTEM classifies it as living. Technically."
    ),
)

# Tier 4 -- void palace / cozy-sinister

_NULL_WINDOW = UpgradeOption(
    slug="null-window",
    name="Null Window",
    tier=_TIER_4_MIN_LEVEL,
    description=(
        "A window that opens onto void. Not darkness -- void. The"
        " distinction matters. A faint warmth comes through. THE SYSTEM"
        " recommends not leaning on the frame."
    ),
)

_ORBITAL_INSTANCE = UpgradeOption(
    slug="orbital-instance",
    name="Orbital Instance",
    tier=_TIER_4_MIN_LEVEL,
    description=(
        "Floating pixel orb, slow rotation, no visible means of"
        " suspension. It moves slightly faster when no one is watching."
        " THE SYSTEM has confirmed this. THE SYSTEM will not confirm it again."
    ),
)

_EXCESSIVE_THRONE = UpgradeOption(
    slug="excessive-throne",
    name="Excessive Throne",
    tier=_TIER_4_MIN_LEVEL,
    description=(
        "A throne. Too large for the room. Too large for any room. It"
        " was not brought in through the door. THE SYSTEM has no record"
        " of its installation. THE SYSTEM is comfortable with this."
    ),
)

# ---------------------------------------------------------------------------
# Public catalog
# ---------------------------------------------------------------------------

ROOM_CATALOG: tuple[UpgradeOption, ...] = (
    # Tier 1
    _ARCHIVE_INSTANCE,
    _CIVIC_GRAFT,
    _SALVAGE_SHELF,
    # Tier 2
    _DEFIANT_GLOW,
    _QUESTIONABLE_COMFORT,
    _THERMAL_EVENT,
    # Tier 3
    _AMBIENT_SURVEILLANCE,
    _PERSISTENT_PRESENCE,
    _WILTING_SIGNAL,
    # Tier 4
    _NULL_WINDOW,
    _ORBITAL_INSTANCE,
    _EXCESSIVE_THRONE,
)
"""All room upgrades, ordered by tier then position.

Pass this to :func:`sender_frenz.common.levels.room_options_for_level` or
:func:`sender_frenz.common.levels.apply_level_up` as the ``room_catalog``
argument.
"""


# ---------------------------------------------------------------------------
# Convenience query
# ---------------------------------------------------------------------------


def rooms_for_level(level: int) -> tuple[UpgradeOption, ...]:
    """Return all room upgrades whose tier is at or below *level*.

    This is a catalog-side convenience function that does **not** filter
    already-applied slugs.  For the full level-up flow (which also excludes
    previously applied upgrades), use
    :func:`sender_frenz.common.levels.room_options_for_level` with the room.

    Args:
        level: The room's current level.  Values below 1 return an empty
            tuple because no upgrade requires level 0 or below.

    Returns:
        A tuple of :class:`~sender_frenz.common.levels.UpgradeOption` instances
        ordered by tier then by their position in :data:`ROOM_CATALOG`.
    """
    return tuple(opt for opt in ROOM_CATALOG if opt.tier <= level)
