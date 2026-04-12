"""Social-health engine.

Governs the social dimension of avatar health.  Physical care alone keeps an
avatar alive but visually gaunt and vampiric; sustained social interaction
pushes the avatar toward a healthy, expressive appearance.

Modules
-------
interactions
    Interaction event types (visit, gift, chat) and their social-score values.
history
    Per-avatar interaction history: recent events, recency-weighted scoring,
    and the decay that occurs when interactions stop.
effects
    Mapping from social score to vampiric-drift visual parameters, consumed
    by character_builder.appearance.
"""
