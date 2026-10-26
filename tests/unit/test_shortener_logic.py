"""Unit tests for snip.shortener — resolve, stats, list_links, generate_code.

The collision test (create_link + generate_code retry) lives in test_shortener.py.

SLI 3 (resolve correctness): resolve() returns the record for the right code.
SLI 5 (stats accuracy):      resolve() increments clicks; stats() does not.
SLI 4 (create validation):   No URL validation exists yet — no unit tests here;
                              placeholder comment marks where they belong.
"""

import pytest

from snip import shortener
from snip.store import LinkRecord, Store


@pytest.fixture
def fresh_store(monkeypatch):
    s = Store()
    monkeypatch.setattr(shortener, "store", s)
    return s


# ---------------------------------------------------------------------------
# SLI 3 — resolve correctness
# ---------------------------------------------------------------------------

class TestResolve:
    """shortener.resolve must return the record whose URL equals the stored URL."""

    def test_resolve_returns_stored_url(self, fresh_store, monkeypatch):
        """SLI 3: resolved URL equals the URL passed to create_link."""
        monkeypatch.setattr(shortener, "generate_code", lambda: "aaaaaa")
        shortener.create_link("https://example.com/target")
        record = shortener.resolve("aaaaaa")
        assert record.url == "https://example.com/target"

    def test_resolve_unknown_code_raises(self, fresh_store):
        """SLI 2/3: unknown code must raise KeyError so the route handler
        can convert it to a 404 (not a 500)."""
        with pytest.raises(KeyError):
            shortener.resolve("nope00")

    def test_resolve_returns_correct_record_among_many(self, fresh_store, monkeypatch):
        """SLI 3: correct URL returned when multiple links are stored."""
        codes = iter(["aaa111", "bbb222"])
        monkeypatch.setattr(shortener, "generate_code", lambda: next(codes))
        shortener.create_link("https://a.example.com")
        shortener.create_link("https://b.example.com")
        assert shortener.resolve("aaa111").url == "https://a.example.com"
        assert shortener.resolve("bbb222").url == "https://b.example.com"


# ---------------------------------------------------------------------------
# SLI 5 — stats accuracy (click increment)
# ---------------------------------------------------------------------------

class TestClickIncrement:
    """resolve() must increment clicks; stats() must not."""

    def test_resolve_increments_clicks_once(self, fresh_store, monkeypatch):
        """SLI 5: one follow → clicks == 1."""
        monkeypatch.setattr(shortener, "generate_code", lambda: "aaaaaa")
        shortener.create_link("https://example.com")
        shortener.resolve("aaaaaa")
        assert shortener.stats("aaaaaa").clicks == 1

    def test_resolve_increments_clicks_n_times(self, fresh_store, monkeypatch):
        """SLI 5: N follows → clicks == N."""
        monkeypatch.setattr(shortener, "generate_code", lambda: "aaaaaa")
        shortener.create_link("https://example.com")
        for _ in range(5):
            shortener.resolve("aaaaaa")
        assert shortener.stats("aaaaaa").clicks == 5

    def test_stats_does_not_increment_clicks(self, fresh_store, monkeypatch):
        """SLI 5: reading stats must not itself count as a follow."""
        monkeypatch.setattr(shortener, "generate_code", lambda: "aaaaaa")
        shortener.create_link("https://example.com")
        shortener.stats("aaaaaa")
        shortener.stats("aaaaaa")
        assert shortener.stats("aaaaaa").clicks == 0

    def test_clicks_start_at_zero_before_any_resolve(self, fresh_store, monkeypatch):
        """SLI 5: a newly created link has 0 clicks."""
        monkeypatch.setattr(shortener, "generate_code", lambda: "aaaaaa")
        shortener.create_link("https://example.com")
        assert shortener.stats("aaaaaa").clicks == 0

    def test_stats_unknown_code_raises(self, fresh_store):
        """SLI 2: unknown code in stats must raise KeyError → 404 at route level."""
        with pytest.raises(KeyError):
            shortener.stats("nope00")


# ---------------------------------------------------------------------------
# generate_code — code format
# ---------------------------------------------------------------------------

class TestGenerateCode:
    """generate_code() must produce codes of the right length and character set.
    Not an SLI gate, but a wrong format here would corrupt every SLI."""

    def test_code_length(self):
        assert len(shortener.generate_code()) == shortener.CODE_LENGTH

    def test_code_uses_only_alphabet_characters(self):
        for _ in range(50):
            code = shortener.generate_code()
            assert all(c in shortener.ALPHABET for c in code)

    def test_codes_are_not_all_identical(self):
        """Trivial entropy check — not a statistical test, just a smoke check
        that the generator is not returning a constant."""
        codes = {shortener.generate_code() for _ in range(20)}
        assert len(codes) > 1


# ---------------------------------------------------------------------------
# list_links
# ---------------------------------------------------------------------------

class TestListLinks:
    """list_links() surfaces all stored records to employees."""

    def test_list_empty_on_fresh_store(self, fresh_store):
        assert shortener.list_links() == []

    def test_list_returns_all_created_links(self, fresh_store, monkeypatch):
        codes = iter(["aaa111", "bbb222"])
        monkeypatch.setattr(shortener, "generate_code", lambda: next(codes))
        shortener.create_link("https://a.example.com")
        shortener.create_link("https://b.example.com")
        urls = {r.url for r in shortener.list_links()}
        assert urls == {"https://a.example.com", "https://b.example.com"}


# ---------------------------------------------------------------------------
# SLI 4 — create validation (placeholder)
# ---------------------------------------------------------------------------
# URL validation does not exist yet (finding #2 — left open in PR #1).
# Unit tests for scheme allow-list, empty-string rejection, bare-word rejection,
# and script-scheme rejection belong here once models.py / create_link gains
# that logic.
