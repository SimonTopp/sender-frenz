"""Social interaction actions.

These are the three player-facing interactions for building social health.
All functions are pure: they take current state plus a timestamp and return
new avatar state plus a THE SYSTEM quip.

No I/O, no randomness of their own.  Callers supply the current timestamp
and a :data:`~sender_frenz.common.quips.QuipCaller`.

Vampiric retreat
----------------
:func:`interact` boosts ``social.score`` and stamps ``last_interaction``;
it does **not** advance or retreat the vampiric stage.  Stage retreat is
computed by :func:`~sender_frenz.common.decay.apply_social_decay` on the
next decay tick, based on elapsed time and the (now positive) score.
This keeps the decay model centralised and avoids double-counting.

Score ceiling
-------------
There is no over-socialization penalty.  Social score simply clamps at
``1.0``; unlike hunger and hygiene there is no *ideal maximum* above which
extra decay fires.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from sender_frenz.common.models import Avatar, SocialState
from sender_frenz.common.quips import QuipTrigger

if TYPE_CHECKING:
    from sender_frenz.common.quips import QuipCaller
    from sender_frenz.common.types import Timestamp

# ---------------------------------------------------------------------------
# Interaction kinds
# ---------------------------------------------------------------------------


class InteractionKind(StrEnum):
    """The three social interaction types available to players.

    Attributes:
        VISIT: Avatar visited another avatar, or received a visitor.
            Highest social-score boost; involves physical co-presence.
        GIFT: Gift sent or received.
            Mid-tier boost; a material gesture of social investment.
        CHAT: Message sent or received.
            Smallest boost; lightweight but still meaningful contact.
    """

    VISIT = "visit"
    GIFT = "gift"
    CHAT = "chat"


# ---------------------------------------------------------------------------
# Score boost constants
# ---------------------------------------------------------------------------

VISIT_SCORE_BOOST: float = 0.25
"""Social score restored by a single visit interaction (Meter units)."""

GIFT_SCORE_BOOST: float = 0.15
"""Social score restored by a single gift interaction (Meter units)."""

CHAT_SCORE_BOOST: float = 0.05
"""Social score restored by a single chat interaction (Meter units)."""

# Internal mapping — keeps interact() free of a match statement.
_BOOST: dict[InteractionKind, float] = {
    InteractionKind.VISIT: VISIT_SCORE_BOOST,
    InteractionKind.GIFT: GIFT_SCORE_BOOST,
    InteractionKind.CHAT: CHAT_SCORE_BOOST,
}

# QuipTrigger values match InteractionKind values, so we can map directly.
_TRIGGER: dict[InteractionKind, QuipTrigger] = {
    InteractionKind.VISIT: QuipTrigger.VISIT,
    InteractionKind.GIFT: QuipTrigger.GIFT,
    InteractionKind.CHAT: QuipTrigger.CHAT,
}

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InteractionResult:
    """The outcome of a social interaction.

    Attributes:
        avatar: Updated avatar state after the interaction.
        quip: THE SYSTEM's comment on the interaction, selected by the
            caller's :data:`~sender_frenz.common.quips.QuipCaller`.
    """

    avatar: Avatar
    quip: str


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------


def interact(
    avatar: Avatar,
    kind: InteractionKind,
    now: Timestamp,
    quip_caller: QuipCaller,
) -> InteractionResult:
    """Record a social interaction and boost the avatar's social score.

    Social score is boosted by the amount associated with *kind* and clamped
    to ``1.0``.  ``social.last_interaction`` is updated to *now* so the decay
    engine has a fresh reference point for subsequent ticks.

    The vampiric stage is not modified here.  Stage retreat is handled by
    :func:`~sender_frenz.common.decay.apply_social_decay` on the next tick.

    Args:
        avatar: Current avatar state.
        kind: The type of social interaction that occurred.
        now: Current timestamp (Unix epoch seconds), recorded as
            ``social.last_interaction``.
        quip_caller: Quip delivery callable.

    Returns:
        An :class:`InteractionResult` with the updated avatar and a quip.
    """
    new_score = min(1.0, avatar.social.score + _BOOST[kind])
    new_social = SocialState(
        score=new_score,
        vampiric_stage=avatar.social.vampiric_stage,
        last_interaction=now,
    )
    new_avatar = Avatar(
        id=avatar.id,
        needs=avatar.needs,
        social=new_social,
        level=avatar.level,
        created_at=avatar.created_at,
    )
    return InteractionResult(avatar=new_avatar, quip=quip_caller(_TRIGGER[kind]))
