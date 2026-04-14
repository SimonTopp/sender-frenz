"""Game loop: session and tick engine.

The only module permitted to import from multiple sibling packages.
Composes the five engine modules into a unified session model.

Modules
-------
tick
    Headless state-advancement engine.  Applies time-based decay and
    records what changed as a :class:`~tick.GameEvent` log — the
    canonical animation contract for the display layer.
    Key exports: :func:`~tick.process_tick`,
    :class:`~tick.TickResult`, :class:`~tick.GameEvent`,
    :class:`~tick.GameEventKind`.
session
    Player-session model.  Composes :func:`~tick.process_tick` with
    status summaries, level-up eligibility, and quip collection into
    a single :class:`~session.SessionState` bundle.
    Key exports: :func:`~session.open_session`,
    :class:`~session.SessionState`.
"""
