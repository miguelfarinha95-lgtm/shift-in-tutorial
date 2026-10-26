"""Unit tests for snip.store — in-memory persistence layer.

SLI 3 (resolve correctness): Store.put/get must return the exact record stored.
SLI 5 (stats accuracy):      Store.get returns the live object; mutations via
                              the returned reference are reflected on the next get.
"""

import pytest

from snip.store import LinkRecord, Store


@pytest.fixture
def s():
    return Store()


def make_record(code="aaaaaa", url="https://example.com", clicks=0):
    return LinkRecord(code=code, url=url, clicks=clicks)


# ---------------------------------------------------------------------------
# SLI 3 — resolve correctness
# ---------------------------------------------------------------------------

class TestStoreGet:
    """Store.get must return the exact record that was put."""

    def test_get_returns_stored_url(self, s):
        """SLI 3: retrieved URL equals the stored URL byte-for-byte."""
        r = make_record(url="https://example.com/exact")
        s.put(r)
        assert s.get("aaaaaa").url == "https://example.com/exact"

    def test_get_returns_stored_code(self, s):
        """SLI 3: retrieved code equals the key used to store it."""
        r = make_record(code="xyz999")
        s.put(r)
        assert s.get("xyz999").code == "xyz999"

    def test_get_unknown_code_raises_key_error(self, s):
        """SLI 2 (availability): unknown code must raise KeyError, not silently
        return None — callers (route handlers) convert KeyError to 404."""
        with pytest.raises(KeyError):
            s.get("nope00")

    def test_get_returns_the_right_record_among_many(self, s):
        """SLI 3: correct record is returned when several are stored."""
        s.put(make_record(code="aaa111", url="https://a.example.com"))
        s.put(make_record(code="bbb222", url="https://b.example.com"))
        s.put(make_record(code="ccc333", url="https://c.example.com"))
        assert s.get("bbb222").url == "https://b.example.com"


class TestStoreExists:
    """Store.exists must reflect what has been put — used by create_link retry."""

    def test_exists_true_after_put(self, s):
        s.put(make_record(code="aaaaaa"))
        assert s.exists("aaaaaa") is True

    def test_exists_false_for_unknown(self, s):
        assert s.exists("nope00") is False

    def test_exists_false_after_fresh_store(self, s):
        """Each Store() starts empty — no state leaks from other tests."""
        assert s.exists("aaaaaa") is False


# ---------------------------------------------------------------------------
# SLI 5 — stats accuracy
# ---------------------------------------------------------------------------

class TestClickCountMutability:
    """Store.get returns the live object; incrementing clicks on the returned
    reference must be visible on the next get (how shortener.resolve works)."""

    def test_click_increment_is_visible_on_subsequent_get(self, s):
        """SLI 5: mutation via one get reference is reflected by a second get."""
        r = make_record()
        s.put(r)
        s.get("aaaaaa").clicks += 1
        assert s.get("aaaaaa").clicks == 1

    def test_initial_clicks_is_zero(self, s):
        """SLI 5: brand-new record starts at 0 clicks."""
        s.put(make_record())
        assert s.get("aaaaaa").clicks == 0


# ---------------------------------------------------------------------------
# Store.all — used by list_links()
# ---------------------------------------------------------------------------

class TestStoreAll:
    """Store.all returns every stored record — not an SLI gate itself, but
    wrong results here would misrepresent link inventory to employees."""

    def test_all_empty_on_fresh_store(self, s):
        assert s.all() == []

    def test_all_returns_all_records(self, s):
        s.put(make_record(code="aaa111"))
        s.put(make_record(code="bbb222"))
        codes = {r.code for r in s.all()}
        assert codes == {"aaa111", "bbb222"}

    def test_all_returns_a_copy_not_the_internal_dict(self, s):
        """Mutating the returned list must not affect the store."""
        s.put(make_record(code="aaa111"))
        s.all().clear()
        assert len(s.all()) == 1
