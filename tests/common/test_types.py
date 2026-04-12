"""Tests for sender_frenz.common.types."""

from uuid import UUID, uuid4

from sender_frenz.common.types import AvatarId, Decayable, RoomId, Upgradeable


class TestNewTypes:
    def test_avatar_id_wraps_uuid(self) -> None:
        raw = uuid4()
        avatar_id = AvatarId(raw)
        assert avatar_id == raw

    def test_room_id_wraps_uuid(self) -> None:
        raw = uuid4()
        room_id = RoomId(raw)
        assert room_id == raw

    def test_avatar_id_and_room_id_are_distinct_types(self) -> None:
        raw = UUID("12345678-1234-5678-1234-567812345678")
        avatar_id = AvatarId(raw)
        room_id = RoomId(raw)
        # Both wrap the same UUID value but are different NewType wrappers.
        assert avatar_id == room_id  # value equality still holds at runtime


class TestDecayableProtocol:
    def test_conforming_class_is_recognised(self) -> None:
        class HasLastUpdated:
            last_updated: float = 0.0

        assert isinstance(HasLastUpdated(), Decayable)

    def test_non_conforming_class_is_rejected(self) -> None:
        class MissingField:
            pass

        assert not isinstance(MissingField(), Decayable)


class TestUpgradeableProtocol:
    def test_conforming_class_is_recognised(self) -> None:
        class HasLevelAndUpgrades:
            level: int = 0
            applied_upgrades: tuple[str, ...] = ()

        assert isinstance(HasLevelAndUpgrades(), Upgradeable)

    def test_non_conforming_class_is_rejected(self) -> None:
        class OnlyLevel:
            level: int = 0

        assert not isinstance(OnlyLevel(), Upgradeable)
