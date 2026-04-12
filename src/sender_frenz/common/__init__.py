"""Shared foundations used by every other sender-frenz module.

This package must not import from any sibling package (character_builder,
space_builder, required_maintenance, social_maintenance).  All other packages
may freely import from here.

Modules
-------
models
    Core dataclasses: Avatar, Room, NeedState, SocialState, Level.
decay
    Time-based need-decay engine: calculates meter deltas given elapsed time.
levels
    Level thresholds, unlock catalog, and progression rules.
types
    Shared type aliases and Protocols (e.g. Decayable, Upgradeable).
"""
