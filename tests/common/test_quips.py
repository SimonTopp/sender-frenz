"""Tests for sender_frenz.common.quips."""

import random

from sender_frenz.common.quips import (
    _QUIPS,
    QuipCaller,
    QuipCallerProtocol,
    QuipTrigger,
    default_quip_caller,
)


class TestQuipTrigger:
    def test_all_expected_triggers_defined(self) -> None:
        names = {t.name for t in QuipTrigger}
        expected = {
            "FEED",
            "CLEAN",
            "OVER_NOURISHED",
            "OVER_SCRUBBED",
            "HUNGER_WARNING",
            "HUNGER_CRITICAL",
            "HYGIENE_WARNING",
            "HYGIENE_CRITICAL",
            "SOCIAL_WARNING",
            "SOCIAL_CRITICAL",
            "LOGIN",
            "VISIT",
            "GIFT",
            "CHAT",
        }
        assert names == expected

    def test_trigger_values_are_strings(self) -> None:
        for trigger in QuipTrigger:
            assert isinstance(trigger.value, str)

    def test_quip_pool_covers_every_trigger(self) -> None:
        for trigger in QuipTrigger:
            assert trigger in _QUIPS, f"{trigger} missing from _QUIPS"

    def test_each_pool_has_at_least_three_quips(self) -> None:
        for trigger, pool in _QUIPS.items():
            assert len(pool) >= 3, f"{trigger} pool has only {len(pool)} quip(s)"


class TestDefaultQuipCaller:
    def test_returns_string_for_every_trigger(self) -> None:
        caller = default_quip_caller(rng=random.Random(0))
        for trigger in QuipTrigger:
            result = caller(trigger)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_seeded_rng_is_deterministic(self) -> None:
        caller_a = default_quip_caller(rng=random.Random(42))
        caller_b = default_quip_caller(rng=random.Random(42))
        for trigger in QuipTrigger:
            assert caller_a(trigger) == caller_b(trigger)

    def test_unseeded_caller_returns_string(self) -> None:
        caller = default_quip_caller()
        result = caller(QuipTrigger.FEED)
        assert isinstance(result, str)

    def test_seeded_caller_with_none_uses_fresh_rng(self) -> None:
        # Two callers with None rng are independent (different seeds).
        # We just verify they run without error and return strings.
        caller = default_quip_caller(rng=None)
        assert isinstance(caller(QuipTrigger.LOGIN), str)

    def test_quip_caller_type_alias_is_callable(self) -> None:
        # QuipCaller is a Callable type alias; default_quip_caller satisfies it.
        caller: QuipCaller = default_quip_caller(rng=random.Random(1))
        assert callable(caller)

    def test_satisfies_quip_caller_protocol(self) -> None:
        caller = default_quip_caller(rng=random.Random(7))
        assert isinstance(caller, QuipCallerProtocol)

    def test_quips_come_from_pool(self) -> None:
        # Every result across varied seeds must be drawn from the pool.
        pool = set(_QUIPS[QuipTrigger.FEED])
        for seed in range(20):
            c = default_quip_caller(rng=random.Random(seed))
            result = c(QuipTrigger.FEED)
            assert result in pool
