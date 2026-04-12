"""Shared type aliases and structural protocols.

Import these in any module that works with avatar or room identifiers,
meter values, or timestamps.  Prefer these aliases over bare primitives
so that type checkers can catch unit confusion early.
"""

from __future__ import annotations

from typing import NewType, Protocol, runtime_checkable
from uuid import UUID

# ---------------------------------------------------------------------------
# Scalar aliases
# ---------------------------------------------------------------------------

AvatarId = NewType("AvatarId", UUID)
"""Unique identifier for an avatar."""

RoomId = NewType("RoomId", UUID)
"""Unique identifier for a room."""

Meter = float
"""A value in the closed interval [0.0, 1.0].

0.0 means completely empty / depleted.
1.0 means completely full / healthy.

The type system cannot enforce the range at runtime; callers must clamp.
"""

Timestamp = float
"""Unix epoch time in seconds (UTC), as returned by ``time.time()``.

Production code must never call ``time.time()`` directly inside
``common``.  Callers compute elapsed time and pass it in explicitly.
"""

# ---------------------------------------------------------------------------
# Structural protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class Decayable(Protocol):
    """Anything whose state degrades over time.

    Implementors do not need to inherit from this class; structural
    compatibility is sufficient.
    """

    last_updated: Timestamp


@runtime_checkable
class Upgradeable(Protocol):
    """Anything that accumulates upgrades as levels increase.

    Implementors do not need to inherit from this class; structural
    compatibility is sufficient.
    """

    level: int
    applied_upgrades: tuple[str, ...]
