"""Tests for sender_frenz.character_builder.avatar."""

from uuid import uuid4

import pytest

from sender_frenz.character_builder.avatar import (
    INITIAL_METER,
    SKELETON_LEVEL,
    create_avatar,
)
from sender_frenz.common.models import Avatar, VampiricStage
from sender_frenz.common.types import AvatarId

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW: float = 1_000_000.0  # arbitrary timestamp


def _new_id() -> AvatarId:
    return AvatarId(uuid4())


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestSkeletonConstants:
    def test_skeleton_level_is_zero(self) -> None:
        assert SKELETON_LEVEL == 0

    def test_initial_meter_is_one(self) -> None:
        assert pytest.approx(1.0) == INITIAL_METER


# ---------------------------------------------------------------------------
# create_avatar — return type
# ---------------------------------------------------------------------------


class TestCreateAvatarReturnType:
    def test_returns_avatar_instance(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert isinstance(avatar, Avatar)


# ---------------------------------------------------------------------------
# create_avatar — identity fields
# ---------------------------------------------------------------------------


class TestCreateAvatarIdentity:
    def test_avatar_id_preserved(self) -> None:
        aid = _new_id()
        avatar = create_avatar(aid, _NOW)
        assert avatar.id == aid

    def test_created_at_equals_now(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert pytest.approx(_NOW) == avatar.created_at

    def test_different_ids_produce_independent_avatars(self) -> None:
        id_a = _new_id()
        id_b = _new_id()
        assert id_a != id_b
        av_a = create_avatar(id_a, _NOW)
        av_b = create_avatar(id_b, _NOW)
        assert av_a.id != av_b.id
        # All other fields should be equal (same timestamp, same defaults)
        assert pytest.approx(av_a.needs.hunger) == av_b.needs.hunger
        assert av_a.level == av_b.level


# ---------------------------------------------------------------------------
# create_avatar — need state
# ---------------------------------------------------------------------------


class TestCreateAvatarNeedState:
    def test_initial_hunger_is_full(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert pytest.approx(INITIAL_METER) == avatar.needs.hunger

    def test_initial_hygiene_is_full(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert pytest.approx(INITIAL_METER) == avatar.needs.hygiene

    def test_needs_last_updated_equals_now(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert pytest.approx(_NOW) == avatar.needs.last_updated


# ---------------------------------------------------------------------------
# create_avatar — social state
# ---------------------------------------------------------------------------


class TestCreateAvatarSocialState:
    def test_initial_social_score_is_full(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert pytest.approx(INITIAL_METER) == avatar.social.score

    def test_vampiric_stage_is_none(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert avatar.social.vampiric_stage is VampiricStage.NONE

    def test_social_last_interaction_equals_now(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert pytest.approx(_NOW) == avatar.social.last_interaction


# ---------------------------------------------------------------------------
# create_avatar — level state
# ---------------------------------------------------------------------------


class TestCreateAvatarLevelState:
    def test_level_current_is_skeleton_level(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert avatar.level.current == SKELETON_LEVEL

    def test_no_skin_upgrades_on_creation(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert avatar.level.skin_upgrades == ()

    def test_no_room_upgrades_on_creation(self) -> None:
        avatar = create_avatar(_new_id(), _NOW)
        assert avatar.level.room_upgrades == ()


# ---------------------------------------------------------------------------
# create_avatar — timestamp consistency
# ---------------------------------------------------------------------------


class TestCreateAvatarTimestamps:
    def test_all_timestamps_equal_now(self) -> None:
        """created_at, needs.last_updated, and social.last_interaction all == now."""
        now = 9_999.5
        avatar = create_avatar(_new_id(), now)
        assert pytest.approx(now) == avatar.created_at
        assert pytest.approx(now) == avatar.needs.last_updated
        assert pytest.approx(now) == avatar.social.last_interaction

    def test_zero_timestamp_accepted(self) -> None:
        avatar = create_avatar(_new_id(), 0.0)
        assert pytest.approx(0.0) == avatar.created_at

    def test_large_timestamp_accepted(self) -> None:
        future = 9_999_999_999.0
        avatar = create_avatar(_new_id(), future)
        assert pytest.approx(future) == avatar.created_at


# ---------------------------------------------------------------------------
# create_avatar — immutability (frozen dataclass)
# ---------------------------------------------------------------------------


class TestCreateAvatarImmutability:
    def test_avatar_is_frozen(self) -> None:
        import dataclasses

        avatar = create_avatar(_new_id(), _NOW)
        assert dataclasses.is_dataclass(avatar)
        with pytest.raises(dataclasses.FrozenInstanceError):
            avatar.created_at = 0.0  # type: ignore[misc]
