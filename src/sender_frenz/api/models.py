"""Pydantic request and response models for the sender-frenz API.

These models are the HTTP transport layer.  They are independent of the
persistence serialisation models in :mod:`sender_frenz.persistence.serialization`
— the two representations may diverge as the API and storage formats evolve
separately.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Action kind
# ---------------------------------------------------------------------------


class ActionKind(StrEnum):
    """The five player-facing action types exposed by the API.

    FastAPI validates path parameters against this enum and returns 422
    for unrecognised values.

    Attributes:
        FEED: Feed the avatar (required maintenance).
        CLEAN: Clean the avatar (required maintenance).
        VISIT: Record a visit interaction (social maintenance).
        GIFT: Record a gift interaction (social maintenance).
        CHAT: Record a chat interaction (social maintenance).
    """

    FEED = "feed"
    CLEAN = "clean"
    VISIT = "visit"
    GIFT = "gift"
    CHAT = "chat"


# ---------------------------------------------------------------------------
# Sub-models shared across responses
# ---------------------------------------------------------------------------


class NeedsResponse(BaseModel):
    """Raw need meter values for an avatar."""

    hunger: float
    hygiene: float


class SocialResponse(BaseModel):
    """Raw social state for an avatar."""

    score: float
    vampiric_stage: str


class LevelResponse(BaseModel):
    """Avatar progression state."""

    current: int
    skin_upgrades: list[str]
    room_upgrades: list[str]


class NeedsSummaryResponse(BaseModel):
    """Computed boolean flags derived from the avatar's need meters."""

    hunger: float
    hygiene: float
    hungry: bool
    dirty: bool
    over_nourished: bool
    over_scrubbed: bool


class SocialSummaryResponse(BaseModel):
    """Computed social status flags and labels."""

    score: float
    vampiric_stage: str
    is_isolated: bool
    is_thriving: bool
    stage_label: str


class AppearanceResponse(BaseModel):
    """Display-ready visual state derived from the avatar."""

    vampiric_stage: str
    hunger_visual: str
    hygiene_visual: str
    skin_slug: str | None
    composite_label: str


class GameEventResponse(BaseModel):
    """A single state-change event emitted during a tick."""

    kind: str
    timestamp: float


class UpgradeOptionResponse(BaseModel):
    """A single skin or room upgrade option."""

    slug: str
    name: str
    tier: int
    description: str


# ---------------------------------------------------------------------------
# Top-level response models
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    """Full payload returned by POST /session/open."""

    avatar_id: str
    needs: NeedsResponse
    social: SocialResponse
    level: LevelResponse
    needs_summary: NeedsSummaryResponse
    social_summary: SocialSummaryResponse
    appearance: AppearanceResponse
    level_up_available: bool
    events: list[GameEventResponse]
    quips: list[str]


class ActionResponse(BaseModel):
    """Payload returned by POST /action/{kind}."""

    avatar_id: str
    needs: NeedsResponse
    social: SocialResponse
    quip: str


class LevelUpRequest(BaseModel):
    """Request body for POST /level-up."""

    skin_slug: str
    room_slug: str


class LevelUpResponse(BaseModel):
    """Payload returned by POST /level-up."""

    avatar_id: str
    level: LevelResponse
    skin_options: list[UpgradeOptionResponse]
    room_options: list[UpgradeOptionResponse]


class AvatarResponse(BaseModel):
    """Payload returned by GET /avatar/{id}."""

    avatar_id: str
    needs: NeedsResponse
    social: SocialResponse
    level: LevelResponse
    sustained_since: float | None
    last_tick: float
