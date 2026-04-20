"""Canonical meter thresholds shared across sender-frenz modules.

Centralized here so the decay, action, appearance, and needs-query layers
all agree on what counts as ``ideal``, ``mid``, or ``critical``.  No other
module should redefine these values — import from here instead.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Ideal-maximum thresholds
# ---------------------------------------------------------------------------

HUNGER_IDEAL_MAX: float = 0.80
"""Hunger above this value is over-nourished (visual + decay penalty)."""

HYGIENE_IDEAL_MAX: float = 0.90
"""Hygiene above this value is over-scrubbed (visual + decay penalty)."""

# ---------------------------------------------------------------------------
# Midpoints between ideal and critical (visual bucketing only)
# ---------------------------------------------------------------------------

HUNGER_MID: float = 0.50
"""Boundary between ``"nourished"`` and ``"hungry"`` visual buckets."""

HYGIENE_MID: float = 0.60
"""Boundary between ``"clean"`` and ``"unkempt"`` visual buckets."""

# ---------------------------------------------------------------------------
# Critical thresholds
# ---------------------------------------------------------------------------

HUNGER_CRITICAL: float = 0.20
"""Hunger at or below this value is critical (``"starved"`` visual)."""

HYGIENE_CRITICAL: float = 0.20
"""Hygiene at or below this value is critical (``"grimy"`` visual)."""
