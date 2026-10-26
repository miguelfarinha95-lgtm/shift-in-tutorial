"""HTTP integration tests for snip routes.

Each test asserts status code and response structure only.
Input-validation cases belong in tests/unit/test_models.py.

Fixture: a per-test fresh Store is swapped in via monkeypatch so the global
singleton never leaks state between tests (CLAUDE.md working agreement).
"""

import pytest
from fastapi.testclient import TestClient

from snip import shortener
from snip.main import app
from snip.store import Store

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    """TestClient wired to a fresh Store for every test."""
    monkeypatch.setattr(shortener, "store", Store())
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client_with_link(monkeypatch):
    """TestClient pre-loaded with one link (code fixed to 'aaaaaa')."""
    s = Store()
    monkeypatch.setattr(shortener, "store", s)
    monkeypatch.setattr(shortener, "generate_code", lambda: "aaaaaa")
    c = TestClient(app, raise_server_exceptions=False)
    c.post("/api/links", json={"url": "https://example.com/target"})
    return c


# ---------------------------------------------------------------------------
# POST /api/links
# ---------------------------------------------------------------------------

class TestCreateLink:
    def test_returns_201(self, client):
        """SLI 4: a valid create request must return 201 Created."""
        resp = client.post("/api/links", json={"url": "https://example.com"})
        assert resp.status_code == 201

    def test_response_contains_code_url_clicks(self, client):
        """SLI 3/5: response body must contain code, url, and clicks."""
        resp = client.post("/api/links", json={"url": "https://example.com"})
        body = resp.json()
        assert "code" in body
        assert body["url"] == "https://example.com"
        assert body["clicks"] == 0


# ---------------------------------------------------------------------------
# GET /{code}  — the hot path
# ---------------------------------------------------------------------------

class TestFollow:
    def test_known_code_returns_307(self, client_with_link):
        """SLI 2: a known code must redirect with 307 Temporary Redirect."""
        resp = client_with_link.get("/aaaaaa", follow_redirects=False)
        assert resp.status_code == 307

    def test_known_code_location_equals_stored_url(self, client_with_link):
        """SLI 3: Location header must equal the URL that was stored."""
        resp = client_with_link.get("/aaaaaa", follow_redirects=False)
        assert resp.headers["location"] == "https://example.com/target"

    def test_unknown_code_returns_404(self, client):
        """SLI 2: an unknown code must return 404, never 500."""
        resp = client.get("/nope00", follow_redirects=False)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/links/{code}/stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_known_code_returns_200(self, client_with_link):
        """Stats for a known code must return 200."""
        resp = client_with_link.get("/api/links/aaaaaa/stats")
        assert resp.status_code == 200

    def test_response_contains_code_url_clicks(self, client_with_link):
        """SLI 5: stats response must expose code, url, and clicks."""
        resp = client_with_link.get("/api/links/aaaaaa/stats")
        body = resp.json()
        assert body["code"] == "aaaaaa"
        assert body["url"] == "https://example.com/target"
        assert "clicks" in body

    def test_unknown_code_returns_404(self, client):
        """SLI 2: stats for an unknown code must return 404, never 500."""
        resp = client.get("/api/links/nope00/stats")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/links
# ---------------------------------------------------------------------------

class TestListLinks:
    def test_empty_store_returns_200_and_empty_list(self, client):
        resp = client.get("/api/links")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_list_with_created_link(self, client_with_link):
        """Each item in the list must have code, url, and clicks."""
        resp = client_with_link.get("/api/links")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["code"] == "aaaaaa"
        assert items[0]["url"] == "https://example.com/target"
        assert "clicks" in items[0]
