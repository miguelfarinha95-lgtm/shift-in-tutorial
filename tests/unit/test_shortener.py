"""Unit tests for snip.shortener — code generation and collision handling."""

import pytest

from snip import shortener
from snip.store import Store


@pytest.fixture
def fresh_store(monkeypatch):
    """Replace the global singleton so state does not leak between tests."""
    s = Store()
    monkeypatch.setattr(shortener, "store", s)
    return s


def test_collision_does_not_overwrite_existing_link(fresh_store, monkeypatch):
    """Finding #3: generate_code() has no collision check.

    If the generator hands out a code that is already taken, create_link must
    not silently replace the first owner's link (SLI 3 — resolve correctness,
    SLI 5 — stats accuracy). Force the collision deterministically.
    """
    codes = iter(["abc123", "abc123", "xyz999"])
    monkeypatch.setattr(shortener, "generate_code", lambda: next(codes))

    first = shortener.create_link("https://example.com/first")
    second = shortener.create_link("https://example.com/second")

    # The first link must still resolve to the URL it was created with.
    assert fresh_store.get(first.code).url == "https://example.com/first"
    # The retry must have consumed the next value from the iterator and used it.
    assert second.code == "xyz999"
    # That code must actually be stored and retrievable.
    assert fresh_store.get("xyz999").url == "https://example.com/second"
