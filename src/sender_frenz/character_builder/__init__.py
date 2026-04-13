"""Avatar creation and appearance management.

Handles the full lifecycle of an avatar's visual state: from the initial bare
skeleton through healthy growth, vampiric drift caused by social neglect, and
the cumulative skin upgrades earned at each level.

Modules
-------
avatar
    Avatar factory and initial skeleton state construction.
    Key exports: :func:`~sender_frenz.character_builder.avatar.create_avatar`,
    :data:`~sender_frenz.character_builder.avatar.SKELETON_LEVEL`,
    :data:`~sender_frenz.character_builder.avatar.INITIAL_METER`.
appearance
    Appearance model: how physical and social health stats map to visual state.
    Key exports: :func:`~sender_frenz.character_builder.appearance.compute_appearance`,
    :class:`~sender_frenz.character_builder.appearance.AppearanceState`.
catalog
    Skin-upgrade catalog: available clothing, accessories, and expressions
    keyed by level.
    Key exports: :data:`~sender_frenz.character_builder.catalog.SKIN_CATALOG`,
    :func:`~sender_frenz.character_builder.catalog.skins_for_level`.
"""
