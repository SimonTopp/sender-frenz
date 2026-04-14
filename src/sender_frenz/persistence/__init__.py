"""Persistence layer: serialization and storage.

Converts game state to and from plain dicts / JSON and provides a
pluggable storage interface for saving and retrieving snapshots.

Modules
-------
snapshots
    :class:`~snapshots.GameSnapshot` — the canonical save unit bundling
    avatar, room, interaction history, and session-tracking timestamps.
    Key exports: :class:`~snapshots.GameSnapshot`.
serialization
    Pure round-trip conversion functions.  No I/O.
    Key exports: :func:`~serialization.snapshot_to_json`,
    :func:`~serialization.snapshot_from_json`,
    :func:`~serialization.snapshot_to_dict`,
    :func:`~serialization.snapshot_from_dict`.
store
    Storage interface and in-memory implementation.
    Key exports: :class:`~store.StoreProtocol`,
    :class:`~store.MemoryStore`.
"""
