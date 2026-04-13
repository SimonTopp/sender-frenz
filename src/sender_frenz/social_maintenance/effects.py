"""Social health summary and vampiric-stage labels.

:func:`social_summary` is the single entry point.  It takes a current
:class:`~sender_frenz.common.models.Avatar` and returns a :class:`SocialSummary`
dataclass that captures everything a display layer or game-loop needs to act
on the avatar's social state.

This module is the social equivalent of
:mod:`sender_frenz.required_maintenance.needs`: a pure query layer with no
side effects.

Relationship to ``character_builder.appearance``
-------------------------------------------------
The stub docstring describes this module as "consumed by
``character_builder.appearance``".  The consumption is indirect: the
**application layer** passes :attr:`SocialSummary.vampiric_stage` and
:attr:`SocialSummary.stage_label` to the display layer.  No direct import
between ``social_maintenance`` and ``character_builder`` is made;
the no-cross-module-imports rule is preserved.

Threshold mirroring
-------------------
:data:`ISOLATION_THRESHOLD` mirrors the critical threshold in
``sender_frenz.required_maintenance.needs`` (0.20).  It is duplicated
rather than imported to respect the architectural rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sender_frenz.common.models import VampiricStage

if TYPE_CHECKING:
    from sender_frenz.common.models import Avatar

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

ISOLATION_THRESHOLD: float = 0.20
"""Social score at or below this value is considered isolated.

Mirrors the critical threshold in ``sender_frenz.required_maintenance.needs``.
"""

THRIVING_THRESHOLD: float = 0.75
"""Social score strictly above this value is considered thriving.

Aligns with the combined health threshold in
:attr:`sender_frenz.common.levels.LevelConfig.threshold`.
"""

# ---------------------------------------------------------------------------
# Vampiric stage labels (THE SYSTEM voice)
# ---------------------------------------------------------------------------

_STAGE_LABELS: dict[VampiricStage, str] = {
    VampiricStage.NONE: "NOMINAL",
    VampiricStage.PALLOR: "PALLOR ONSET",
    VampiricStage.GAUNT: "STRUCTURAL DRIFT",
    VampiricStage.HOLLOW: "OCULAR VOID",
    VampiricStage.VAMPIRIC: "FULL EXPRESSION",
}
"""THE SYSTEM clinical designation for each vampiric stage.

Used by display layers to label the current drift state without
coupling them to the enum name.
"""

# ---------------------------------------------------------------------------
# SocialSummary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SocialSummary:
    """Snapshot of the avatar's current social health status.

    All fields are computed from the avatar at summary time.

    Attributes:
        score: Current social score in [0.0, 1.0].
        vampiric_stage: Current visual corruption stage.
        is_isolated: ``True`` when score is at or below
            :data:`ISOLATION_THRESHOLD`.
        is_thriving: ``True`` when score is strictly above
            :data:`THRIVING_THRESHOLD`.
        stage_label: THE SYSTEM clinical designation for the current
            vampiric stage.  See :data:`_STAGE_LABELS`.
    """

    score: float
    vampiric_stage: VampiricStage
    is_isolated: bool
    is_thriving: bool
    stage_label: str


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def social_summary(avatar: Avatar) -> SocialSummary:
    """Build a :class:`SocialSummary` from *avatar*'s current social state.

    Args:
        avatar: Current avatar state.

    Returns:
        A :class:`SocialSummary` reflecting the avatar's social health.
    """
    score = avatar.social.score
    stage = avatar.social.vampiric_stage
    return SocialSummary(
        score=score,
        vampiric_stage=stage,
        is_isolated=score <= ISOLATION_THRESHOLD,
        is_thriving=score > THRIVING_THRESHOLD,
        stage_label=_STAGE_LABELS[stage],
    )
