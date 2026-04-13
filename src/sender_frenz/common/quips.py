"""THE SYSTEM voice: quip triggers, caller protocol, and default pool.

All player-facing quips are delivered through a :class:`QuipCaller` so the
delivery mechanism is injectable.  Pass a seeded :class:`random.Random` to
:func:`default_quip_caller` for deterministic output in tests and demos.

Quip content follows the aesthetic guide in ``docs/aesthetic.md``:
corporate, gleefully menacing, clinically off-kilter, ALL-CAPS announcements.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from enum import StrEnum
from typing import Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Trigger enum
# ---------------------------------------------------------------------------


class QuipTrigger(StrEnum):
    """Game events that cause THE SYSTEM to comment.

    Attributes:
        FEED: Player successfully fed the avatar.
        CLEAN: Player successfully cleaned the avatar.
        OVER_NOURISHED: Feed pushed hunger above the ideal maximum.
        OVER_SCRUBBED: Clean pushed hygiene above the ideal maximum.
        HUNGER_WARNING: Hunger meter approaching critical.
        HUNGER_CRITICAL: Hunger meter at or below critical threshold.
        HYGIENE_WARNING: Hygiene meter approaching critical.
        HYGIENE_CRITICAL: Hygiene meter at or below critical threshold.
        SOCIAL_WARNING: Social score approaching critical.
        SOCIAL_CRITICAL: Social score at or below critical threshold.
        LOGIN: Player has started a session.
        VISIT: Avatar visited another avatar, or received a visitor.
        GIFT: Gift sent or received.
        CHAT: Message sent or received.
    """

    FEED = "feed"
    CLEAN = "clean"
    OVER_NOURISHED = "over_nourished"
    OVER_SCRUBBED = "over_scrubbed"
    HUNGER_WARNING = "hunger_warning"
    HUNGER_CRITICAL = "hunger_critical"
    HYGIENE_WARNING = "hygiene_warning"
    HYGIENE_CRITICAL = "hygiene_critical"
    SOCIAL_WARNING = "social_warning"
    SOCIAL_CRITICAL = "social_critical"
    LOGIN = "login"
    VISIT = "visit"
    GIFT = "gift"
    CHAT = "chat"


# ---------------------------------------------------------------------------
# Caller protocol
# ---------------------------------------------------------------------------

QuipCaller = Callable[[QuipTrigger], str]
"""Callable that maps a :class:`QuipTrigger` to a THE SYSTEM quip string.

Implementations must be deterministic for a given trigger when used in
tests.  Use :func:`default_quip_caller` with a seeded
:class:`random.Random` to satisfy this requirement.
"""


@runtime_checkable
class QuipCallerProtocol(Protocol):
    """Structural protocol for :data:`QuipCaller`.

    Any callable ``(trigger: QuipTrigger) -> str`` satisfies this protocol
    and can be used wherever a :data:`QuipCaller` is expected.
    """

    def __call__(self, trigger: QuipTrigger) -> str:  # pragma: no cover
        """Return a quip string for *trigger*.

        Args:
            trigger: The game event that prompted THE SYSTEM to speak.

        Returns:
            A single quip string in THE SYSTEM voice.
        """
        ...


# ---------------------------------------------------------------------------
# Quip pool — minimum three entries per trigger
# ---------------------------------------------------------------------------

_QUIPS: dict[QuipTrigger, tuple[str, ...]] = {
    QuipTrigger.FEED: (
        "NUTRITIONAL INPUT RECEIVED. Caloric reserves updated. THE SYSTEM"
        " notes this intervention with the appropriate level of enthusiasm."
        " Keep it up. Statistically.",
        "FEED EVENT LOGGED. Something has entered the biological processing"
        " pipeline. Tissue density: marginally less alarming. THE SYSTEM"
        " applauds your continued engagement with the survival metric.",
        "INTAKE CONFIRMED. Your avatar has consumed sustenance. Results"
        " pending. THE SYSTEM is cautiously optimistic about your continued"
        " participation.",
    ),
    QuipTrigger.CLEAN: (
        "HYGIENE PROTOCOL EXECUTED. Contaminant load reduced to within"
        " acceptable parameters. HR has been notified. HR is pleased."
        " HR is always pleased when the numbers improve.",
        "CLEANING EVENT LOGGED. Surface-level contamination addressed."
        " Olfactory metrics trending positive. This is what progress looks"
        " like, apparently.",
        "SANITATION CONFIRMED. Your avatar has been processed. Biological"
        " surface readings: improved. THE SYSTEM reminds you that cleanliness"
        " is next to operational efficiency.",
    ),
    QuipTrigger.OVER_NOURISHED: (
        "OVERCONSUMPTION ADVISORY. Caloric intake has exceeded the recommended"
        " operational ceiling. The excess will be managed via accelerated"
        " metabolic processing. This is, technically, fine.",
        "INPUT OVERFLOW DETECTED. Your avatar has been fed past optimal"
        " capacity. THE SYSTEM will implement corrective throughput measures."
        " This is enthusiasm. THE SYSTEM understands enthusiasm.",
        "NUTRITIONAL SURPLUS LOGGED. You have exceeded the caloric ideal."
        " Accelerated drain protocol engaged. THE SYSTEM is not judging."
        " THE SYSTEM is never judging. That is not what THE SYSTEM does.",
    ),
    QuipTrigger.OVER_SCRUBBED: (
        "HYGIENE SATURATION ADVISORY. Cleanliness levels have exceeded"
        " documented optimal parameters. Protective surface layers under"
        " advisory review. You may stop now.",
        "OVER-SANITATION DETECTED. Your avatar is very, extremely clean."
        " Perhaps too clean. THE SYSTEM is engaging corrective protocols."
        " For your avatar's benefit. Certainly.",
        "CLEANLINESS SURPLUS LOGGED. There is a point beyond which cleaning"
        " becomes its own problem. You have located that point. Accelerated"
        " normalization commencing.",
    ),
    QuipTrigger.HUNGER_WARNING: (
        "HUNGER ALERT. Caloric reserves approaching operational minimums."
        " THE SYSTEM recommends a nutritional intervention at your earliest"
        " convenience. The avatar is not complaining. The metrics are"
        " complaining.",
        "NUTRITIONAL ADVISORY ISSUED. Hunger reserves have reached levels"
        " that merit attention. Please feed it. We say this with corporate"
        " warmth and absolutely no urgency.",
        "LOW CALORIC RESERVE DETECTED. Hunger metrics indicate an intervention"
        " opportunity. THE SYSTEM suggests you consider providing sustenance"
        " before the statistics become significantly less comfortable.",
    ),
    QuipTrigger.HUNGER_CRITICAL: (
        "CRITICAL HUNGER DETECTED. Caloric reserves have reached levels that"
        " are, technically, still compatible with continued operation. Bone"
        " density report pending. THE SYSTEM applauds your commitment to the"
        " minimalist lifestyle.",
        "HUNGER TRIAGE PROTOCOL ACTIVE. Your avatar's nutritional situation"
        " has achieved a clinical designation. Tissue integrity metrics are"
        " being compiled. Feed it. Now would be optimal.",
        "CALORIC EMERGENCY LOGGED. Your avatar is operating on reserves that"
        " can be charitably described as trace. THE SYSTEM is fascinated."
        " THE SYSTEM is also filing a report.",
    ),
    QuipTrigger.HYGIENE_WARNING: (
        "HYGIENE ADVISORY. Cleanliness metrics are declining toward a"
        " threshold that Human Resources would describe as a concern."
        " THE SYSTEM recommends corrective action.",
        "SANITATION REMINDER ISSUED. Your avatar's hygiene scores are trending"
        " in a direction that THE SYSTEM finds professionally uncomfortable."
        " Please address this at your earliest convenience.",
        "CONTAMINATION CREEP DETECTED. Surface metrics drifting toward the"
        " lower quartile. This is a courtesy notification. THE SYSTEM remains"
        " supportive of your choices while quietly noting them.",
    ),
    QuipTrigger.HYGIENE_CRITICAL: (
        "HYGIENE CRITICAL. Contamination metrics have entered a range that"
        " THE SYSTEM describes as impressive, in a terrible way. Immediate"
        " remediation is advised. HR is very quiet right now.",
        "SANITATION EMERGENCY LOGGED. Your avatar's hygiene levels have"
        " achieved a distinction that most participants actively avoid."
        " THE SYSTEM is taking notes. Many notes.",
        "CRITICAL CONTAMINATION DETECTED. The numbers are what they are."
        " THE SYSTEM refrains from editorial comment. THE SYSTEM is committed"
        " to a supportive environment. This is very supportive.",
    ),
    QuipTrigger.SOCIAL_WARNING: (
        "ISOLATION ADVISORY. Social contact metrics are declining. Your avatar"
        " has been spending a great deal of time alone. This is observed"
        " without judgment. It is, however, observed.",
        "SOCIAL HEALTH ALERT. Your avatar's interaction metrics are trending"
        " toward a designation THE SYSTEM prefers not to name just yet."
        " Reach out. THE SYSTEM uses the term loosely.",
        "CONTACT DEFICIT DETECTED. Your avatar's social reserves are below"
        " the wellness threshold. THE SYSTEM has initiated a gentle"
        " intervention. THE SYSTEM's interventions are always gentle.",
    ),
    QuipTrigger.SOCIAL_CRITICAL: (
        "ISOLATION ADVISORY. Your avatar has been alone for an extended"
        " period. Hair is doing something interesting. Eyes have developed"
        " an entrepreneurial gleam. THE SYSTEM is not concerned."
        " THE SYSTEM is watching.",
        "SOCIAL EMERGENCY LOGGED. Critical isolation threshold exceeded."
        " Biological changes are in progress. These are natural processes."
        " THE SYSTEM is documenting them. For science.",
        "CRITICAL CONTACT DEFICIT. Your avatar's social score has achieved"
        " a designation we call the drift. Physical alterations are,"
        " technically, a feature. THE SYSTEM presents them as such.",
    ),
    QuipTrigger.LOGIN: (
        "CONTESTANT DETECTED. Welcome back to THE SYSTEM. Your avatar has"
        " been operational in your absence. Metrics were collected."
        " Consequences were logged. Today is a new engagement opportunity.",
        "SESSION INITIATED. THE SYSTEM welcomes you back. Your avatar has"
        " been waiting. It has developed opinions about the wait."
        " THE SYSTEM recommends you address the queue promptly.",
        "PARTICIPANT CONFIRMED. Biometric verification complete. Your avatar's"
        " status has been compiled into a report that is both informative and"
        " mildly concerning. THE SYSTEM looks forward to your review.",
    ),
    QuipTrigger.VISIT: (
        "SOCIAL INTERACTION LOGGED. Physical proximity with another registered"
        " entity has been detected and recorded. Warmth metrics spiking."
        " THE SYSTEM did not see that coming. Updating projections.",
        "VISIT EVENT CONFIRMED. Your avatar has been in the same space as"
        " another avatar. Both parties appear to have survived. THE SYSTEM"
        " notes this outcome as statistically encouraging.",
        "CONTACT PROTOCOL EXECUTED. Another entity entered your avatar's"
        " designated zone and remained there voluntarily. Social score"
        " adjusted upward. THE SYSTEM approves of this development. Cautiously.",
    ),
    QuipTrigger.GIFT: (
        "GIFT TRANSACTION LOGGED. An item has changed hands between registered"
        " participants. The gesture has been classified as prosocial. THE SYSTEM"
        " finds this touching in a way it cannot fully account for.",
        "EXCHANGE EVENT RECORDED. Something was given. Something was received."
        " The metrics improved. THE SYSTEM is choosing not to analyse the"
        " motivations here. Some things are better left unquantified.",
        "MATERIAL TRANSFER CONFIRMED. An object has been conveyed as a gesture"
        " of social investment. Social score updated accordingly. THE SYSTEM"
        " acknowledges that this was, in its way, almost sweet.",
    ),
    QuipTrigger.CHAT: (
        "COMMUNICATION EVENT LOGGED. Text-based contact between participants"
        " has been detected. Social score marginally improved. THE SYSTEM"
        " has read the message. THE SYSTEM has no further comment at this time.",
        "MESSAGE TRANSMISSION CONFIRMED. Words were exchanged. Connections were,"
        " in the loosest possible sense, made. THE SYSTEM notes the effort."
        " THE SYSTEM is not a romantic about effort. But it notes it.",
        "CHAT PROTOCOL EXECUTED. A message has been sent and presumably"
        " received. The social score has been updated to reflect this"
        " minimal but genuine act of reaching out. THE SYSTEM is proud of you.",
    ),
}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def default_quip_caller(rng: random.Random | None = None) -> QuipCaller:
    """Return a :data:`QuipCaller` backed by a randomised quip pool.

    Args:
        rng: Optional seeded :class:`random.Random` instance.  Pass a seeded
            instance in tests to get deterministic quip selection.  When
            ``None``, a freshly created (unseeded) instance is used.

    Returns:
        A :data:`QuipCaller` that selects randomly from the quip pool for
        each trigger.
    """
    _rng = rng if rng is not None else random.Random()

    def _call(trigger: QuipTrigger) -> str:
        return _rng.choice(_QUIPS[trigger])

    return _call
