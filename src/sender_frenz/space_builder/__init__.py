"""Room creation and environment management.

Handles the avatar's personal space: starting as a bare room and accumulating
furnishings and decorations chosen at each level-up.

Modules
-------
room
    Room factory and initial bare-room state construction.
    Key exports: :func:`~sender_frenz.space_builder.room.create_room`,
    :data:`~sender_frenz.space_builder.room.BARE_ROOM_LEVEL`.
catalog
    Space-upgrade catalog: available furniture, lighting, and decor (bean bag
    chairs, lava lamps, plants, posters, etc.) keyed by level.
    Key exports: :data:`~sender_frenz.space_builder.catalog.ROOM_CATALOG`,
    :func:`~sender_frenz.space_builder.catalog.rooms_for_level`.
"""
