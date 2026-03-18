"""Tests for web app database layer."""
from __future__ import annotations

import pytest

from jyotish_app.web.database import (
    create_client,
    get_client,
    get_clients_for_user,
    get_engine,
    get_or_create_user,
    get_user_by_id,
    reset_engine,
)


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    """Use a temp database for every test with full isolation."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    reset_engine()
    get_engine()
    yield
    reset_engine()


class TestUserCrud:
    def test_create_user(self) -> None:
        user = get_or_create_user("g123", "test@test.com", "Test User")
        assert user.id is not None
        assert user.google_id == "g123"
        assert user.email == "test@test.com"

    def test_first_user_becomes_owner(self) -> None:
        user = get_or_create_user("g123", "test@test.com", "First")
        assert user.role == "owner"

    def test_second_user_is_family(self) -> None:
        get_or_create_user("g1", "a@test.com", "First")
        user2 = get_or_create_user("g2", "b@test.com", "Second")
        assert user2.role == "family"

    def test_existing_user_updates_login(self) -> None:
        user1 = get_or_create_user("g123", "a@test.com", "Old Name")
        user2 = get_or_create_user("g123", "a@test.com", "New Name")
        assert user1.id == user2.id
        assert user2.name == "New Name"

    def test_get_user_by_id(self) -> None:
        user = get_or_create_user("g1", "a@test.com", "Test")
        found = get_user_by_id(user.id)
        assert found is not None
        assert found.google_id == "g1"

    def test_get_nonexistent_user(self) -> None:
        assert get_user_by_id(999) is None


class TestClientCrud:
    def test_create_client(self) -> None:
        user = get_or_create_user("g1", "a@test.com", "Test")
        client = create_client(
            user_id=user.id, name="Manish", dob="13/03/1989", tob="12:17",
            place="Varanasi", lat=25.3176, lon=83.0067, gender="Male",
            chart_json='{"lagna_sign": "Mithuna"}',
        )
        assert client.id is not None
        assert client.name == "Manish"

    def test_client_belongs_to_user(self) -> None:
        user = get_or_create_user("g_own", "own@test.com", "Owner")
        create_client(
            user_id=user.id, name="MyClient", dob="01/01/2000", tob="06:00",
            place="Delhi", lat=28.6, lon=77.2, gender="Male", chart_json="{}",
        )
        clients = get_clients_for_user(user.id)
        assert len(clients) == 1
        assert clients[0].name == "MyClient"

    def test_other_user_sees_nothing(self) -> None:
        user1 = get_or_create_user("g1", "a@test.com", "A")
        user2 = get_or_create_user("g2", "b@test.com", "B")
        create_client(
            user_id=user1.id, name="A's client", dob="01/01/2000", tob="06:00",
            place="Delhi", lat=28.6, lon=77.2, gender="Male", chart_json="{}",
        )
        assert len(get_clients_for_user(user2.id)) == 0

    def test_get_client(self) -> None:
        user = get_or_create_user("g1", "a@test.com", "Test")
        client = create_client(
            user_id=user.id, name="Test", dob="01/01/2000", tob="06:00",
            place="Delhi", lat=28.6, lon=77.2, gender="Male", chart_json="{}",
        )
        found = get_client(client.id)
        assert found is not None
        assert found.name == "Test"
