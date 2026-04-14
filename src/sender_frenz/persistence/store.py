"""Storage interface and in-memory implementation.

:class:`StoreProtocol` defines the minimal interface any storage backend
must satisfy.  :class:`MemoryStore` provides a plain dict-backed
implementation suitable for development, testing, and single-process
deployments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sender_frenz.common.types import AvatarId
    from sender_frenz.persistence.snapshots import GameSnapshot


@runtime_checkable
class StoreProtocol(Protocol):
    """Read/write interface for game snapshots.

    Implementations provide the actual storage backend — memory,
    database, object store, etc.  Application code depends only on this
    protocol, not on any concrete implementation.
    """

    def load(self, avatar_id: AvatarId) -> GameSnapshot | None:
        """Return the snapshot for *avatar_id*, or ``None`` if absent.

        Args:
            avatar_id: The avatar whose snapshot to retrieve.

        Returns:
            The stored :class:`~snapshots.GameSnapshot`, or ``None``.
        """
        ...  # pragma: no cover

    def save(self, snapshot: GameSnapshot) -> None:
        """Persist *snapshot*, keyed by ``snapshot.avatar.id``.

        Overwrites any previously stored snapshot for the same avatar ID.

        Args:
            snapshot: The snapshot to persist.
        """
        ...  # pragma: no cover


class MemoryStore:
    """In-memory snapshot store backed by a plain dict.

    Suitable for development, testing, and single-process deployments.
    Not thread-safe; concurrent access must be serialized at the
    application layer.
    """

    def __init__(self) -> None:
        """Initialize an empty snapshot store."""
        self._snapshots: dict[AvatarId, GameSnapshot] = {}

    def load(self, avatar_id: AvatarId) -> GameSnapshot | None:
        """Return the snapshot for *avatar_id*, or ``None`` if absent.

        Args:
            avatar_id: The avatar whose snapshot to retrieve.

        Returns:
            The stored :class:`~snapshots.GameSnapshot`, or ``None``.
        """
        return self._snapshots.get(avatar_id)

    def save(self, snapshot: GameSnapshot) -> None:
        """Persist *snapshot*, keyed by ``snapshot.avatar.id``.

        Overwrites any previously stored snapshot for the same avatar ID.

        Args:
            snapshot: The snapshot to persist.
        """
        self._snapshots[snapshot.avatar.id] = snapshot
