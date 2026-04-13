"""Appearance model: how avatar stats map to visual state.

:func:`compute_appearance` is the single entry point.  It takes a current
:class:`~sender_frenz.common.models.Avatar` and returns an :class:`AppearanceState`
dataclass that captures everything a display layer needs to render the avatar.

No I/O.  No randomness.  Pure stat-to-visual mapping.

Threshold mirroring
-------------------
The hunger and hygiene thresholds defined here intentionally mirror the
constants in ``sender_frenz.required_maintenance.actions``.  They are duplicated
rather than imported to respect the architectural rule that non-``common``
modules do not import from each other.  If these values are ever refactored into
``common``, remove the local definitions and update the imports.

Composite label format
----------------------
The :attr:`AppearanceState.composite_label` is a slash-separated uppercase
string built from whichever components are active::

    # No vampiric drift, no skin:
    "NOURISHED / CLEAN"

    # Vampiric drift present, skin equipped:
    "GAUNT / HUNGRY / UNKEMPT / STATIC GRACE"

Components are included in this order when present:
    1. Vampiric stage (omitted when ``VampiricStage.NONE``)
    2. Hunger visual
    3. Hygiene visual
    4. Skin slug rendered as uppercase with hyphens replaced by spaces
       (omitted when no skin has been applied)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from sender_frenz.common.models import VampiricStage

if TYPE_CHECKING:
    from sender_frenz.common.models import Avatar

# ---------------------------------------------------------------------------
# Threshold constants
# (Mirror required_maintenance.actions — see module docstring.)
# ---------------------------------------------------------------------------

HUNGER_IDEAL_MAX: float = 0.80
"""Hunger above this value is visually over-nourished.

Mirrors ``sender_frenz.required_maintenance.actions.HUNGER_IDEAL_MAX``.
"""

HYGIENE_IDEAL_MAX: float = 0.90
"""Hygiene above this value is visually over-scrubbed.

Mirrors ``sender_frenz.required_maintenance.actions.HYGIENE_IDEAL_MAX``.
"""

HUNGER_CRITICAL: float = 0.20
"""Hunger at or below this value maps to the ``"starved"`` visual.

Mirrors the default critical threshold in
``sender_frenz.required_maintenance.needs``.
"""

HYGIENE_CRITICAL: float = 0.20
"""Hygiene at or below this value maps to the ``"grimy"`` visual.

Mirrors the default critical threshold in
``sender_frenz.required_maintenance.needs``.
"""

# ---------------------------------------------------------------------------
# Visual label types
# ---------------------------------------------------------------------------

HungerVisual = Literal["over_nourished", "nourished", "hungry", "starved"]
"""Display category for the avatar's current hunger level.

Ordered from healthiest to most depleted:

- ``"over_nourished"``: hunger > :data:`HUNGER_IDEAL_MAX` (0.80)
- ``"nourished"``:      hunger in (0.50, :data:`HUNGER_IDEAL_MAX`]
- ``"hungry"``:         hunger in (:data:`HUNGER_CRITICAL`, 0.50]
- ``"starved"``:        hunger ≤ :data:`HUNGER_CRITICAL` (0.20)
"""

HygieneVisual = Literal["over_scrubbed", "clean", "unkempt", "grimy"]
"""Display category for the avatar's current hygiene level.

Ordered from healthiest to most depleted:

- ``"over_scrubbed"``: hygiene > :data:`HYGIENE_IDEAL_MAX` (0.90)
- ``"clean"``:         hygiene in (0.60, :data:`HYGIENE_IDEAL_MAX`]
- ``"unkempt"``:       hygiene in (:data:`HYGIENE_CRITICAL`, 0.60]
- ``"grimy"``:         hygiene ≤ :data:`HYGIENE_CRITICAL` (0.20)
"""

# Midpoint thresholds used by the bucketing helpers.
_HUNGER_MID: float = 0.50
_HYGIENE_MID: float = 0.60


# ---------------------------------------------------------------------------
# AppearanceState
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AppearanceState:
    """A display-ready snapshot of an avatar's current visual state.

    All fields are derived from avatar state at a single point in time.
    This dataclass does not change; call :func:`compute_appearance` again
    when the avatar state updates.

    Attributes:
        vampiric_stage: The avatar's current social-corruption stage.
        hunger_visual: Bucketed hunger display category.
        hygiene_visual: Bucketed hygiene display category.
        skin_slug: Slug of the most recently applied skin upgrade, or
            ``None`` if no skins have been applied yet.
        composite_label: Human-readable, slash-separated uppercase summary
            combining the active visual components.  See the module docstring
            for the exact format.
    """

    vampiric_stage: VampiricStage
    hunger_visual: HungerVisual
    hygiene_visual: HygieneVisual
    skin_slug: str | None
    composite_label: str


# ---------------------------------------------------------------------------
# Bucketing helpers
# ---------------------------------------------------------------------------


def _hunger_visual(hunger: float) -> HungerVisual:
    """Map a hunger meter value to a :data:`HungerVisual` label.

    Args:
        hunger: Current hunger meter value in [0.0, 1.0].

    Returns:
        The corresponding :data:`HungerVisual` bucket.
    """
    if hunger > HUNGER_IDEAL_MAX:
        return "over_nourished"
    if hunger > _HUNGER_MID:
        return "nourished"
    if hunger > HUNGER_CRITICAL:
        return "hungry"
    return "starved"


def _hygiene_visual(hygiene: float) -> HygieneVisual:
    """Map a hygiene meter value to a :data:`HygieneVisual` label.

    Args:
        hygiene: Current hygiene meter value in [0.0, 1.0].

    Returns:
        The corresponding :data:`HygieneVisual` bucket.
    """
    if hygiene > HYGIENE_IDEAL_MAX:
        return "over_scrubbed"
    if hygiene > _HYGIENE_MID:
        return "clean"
    if hygiene > HYGIENE_CRITICAL:
        return "unkempt"
    return "grimy"


def _composite_label(
    vampiric_stage: VampiricStage,
    hunger_visual: HungerVisual,
    hygiene_visual: HygieneVisual,
    skin_slug: str | None,
) -> str:
    """Build the slash-separated composite label from active components.

    Args:
        vampiric_stage: Current corruption stage.
        hunger_visual: Bucketed hunger display category.
        hygiene_visual: Bucketed hygiene display category.
        skin_slug: Most-recently applied skin slug, or ``None``.

    Returns:
        Uppercase slash-separated string containing the active components.
    """
    parts: list[str] = []
    if vampiric_stage is not VampiricStage.NONE:
        parts.append(vampiric_stage.name)
    parts.append(hunger_visual.upper())
    parts.append(hygiene_visual.upper())
    if skin_slug is not None:
        parts.append(skin_slug.replace("-", " ").upper())
    return " / ".join(parts)


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def compute_appearance(avatar: Avatar) -> AppearanceState:
    """Derive a display-ready :class:`AppearanceState` from *avatar*.

    This is a pure function: the same avatar state always produces the same
    appearance.  Call it at render time rather than caching the result, as
    the underlying meters change with each decay tick.

    Args:
        avatar: Current avatar state.

    Returns:
        An :class:`AppearanceState` reflecting the avatar's current visual
        presentation.
    """
    hunger_vis = _hunger_visual(avatar.needs.hunger)
    hygiene_vis = _hygiene_visual(avatar.needs.hygiene)
    skin = avatar.level.skin_upgrades[-1] if avatar.level.skin_upgrades else None
    label = _composite_label(
        vampiric_stage=avatar.social.vampiric_stage,
        hunger_visual=hunger_vis,
        hygiene_visual=hygiene_vis,
        skin_slug=skin,
    )
    return AppearanceState(
        vampiric_stage=avatar.social.vampiric_stage,
        hunger_visual=hunger_vis,
        hygiene_visual=hygiene_vis,
        skin_slug=skin,
        composite_label=label,
    )
