"""Tests for the FastAPI web application."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from jyotish_app.web.database import (
    get_engine,
    get_or_create_user,
    reset_engine,
)


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path):
    """Use temp database."""
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ.pop("GOOGLE_CLIENT_ID", None)
    os.environ.pop("GOOGLE_CLIENT_SECRET", None)
    reset_engine()
    get_engine()
    yield
    reset_engine()
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def app():
    """Create the FastAPI app."""
    from jyotish_app.web.app import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Test client."""
    return TestClient(app)


@pytest.fixture
def auth_client(app):
    """Test client with mocked auth session."""
    user = get_or_create_user("g_test", "test@test.com", "Test User")
    tc = TestClient(app)
    # Manually set session by using cookie
    with tc:
        # Simulate login by setting session data via the session middleware
        # We'll use a helper approach: create a route that sets session
        pass
    return tc, user


class TestHealthCheck:
    def test_health_endpoint(self, client) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestLoginPage:
    def test_unauthenticated_sees_login(self, client) -> None:
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 200
        # Login page should have Google sign-in
        assert "Google" in resp.text or "google" in resp.text

    def test_login_page_has_sacred_header(self, client) -> None:
        resp = client.get("/")
        assert "गणेशाय" in resp.text

    def test_login_page_has_design_system(self, client) -> None:
        resp = client.get("/")
        assert "tokens.css" in resp.text
        assert "components.css" in resp.text


class TestDashboardRequiresAuth:
    def test_dashboard_redirects_when_unauthenticated(self, client) -> None:
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/" in resp.headers.get("location", "")

    def test_new_form_redirects_when_unauthenticated(self, client) -> None:
        resp = client.get("/new", follow_redirects=False)
        assert resp.status_code == 302


class TestStaticFiles:
    def test_tokens_css_accessible(self, client) -> None:
        resp = client.get("/static/tokens.css")
        assert resp.status_code == 200
        assert "j-saffron" in resp.text

    def test_components_css_accessible(self, client) -> None:
        resp = client.get("/static/components.css")
        assert resp.status_code == 200
        assert "j-card" in resp.text

    def test_design_tokens_json_accessible(self, client) -> None:
        resp = client.get("/static/design-tokens.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "color" in data
