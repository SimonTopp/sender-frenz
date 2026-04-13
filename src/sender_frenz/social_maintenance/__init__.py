"""Social-health engine.

Governs the social dimension of avatar health.  Physical care alone keeps an
avatar alive but visually gaunt and vampiric; sustained social interaction
pushes the avatar toward a healthy, expressive appearance.

Modules
-------
interactions
    Interaction event types (visit, gift, chat) and their social-score values.
    Key exports: :func:`~sender_frenz.social_maintenance.interactions.interact`,
    :class:`~sender_frenz.social_maintenance.interactions.InteractionKind`,
    :class:`~sender_frenz.social_maintenance.interactions.InteractionResult`.
history
    Per-avatar interaction history: recent events and window queries.
    Key exports: :func:`~sender_frenz.social_maintenance.history.create_history`,
    :func:`~sender_frenz.social_maintenance.history.add_event`,
    :func:`~sender_frenz.social_maintenance.history.recent_events`,
    :func:`~sender_frenz.social_maintenance.history.interactions_in_window`.
effects
    Social health summary and vampiric-stage labels, consumed by the
    application layer and passed to the display layer.
    Key exports: :func:`~sender_frenz.social_maintenance.effects.social_summary`,
    :class:`~sender_frenz.social_maintenance.effects.SocialSummary`.
"""
