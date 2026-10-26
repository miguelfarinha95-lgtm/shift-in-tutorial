"""Unit tests for snip.models — Pydantic schemas.

SLI 4 (create validation): CreateLinkRequest must accept well-formed input and
                            reject invalid input once validation is added.
SLI 3 (resolve correctness): LinkResponse.from_record must faithfully map every
                              field from a LinkRecord.
"""

import pytest
from pydantic import ValidationError

from snip.models import CreateLinkRequest, LinkResponse
from snip.store import LinkRecord


# ---------------------------------------------------------------------------
# SLI 3 — resolve correctness: LinkResponse.from_record field mapping
# ---------------------------------------------------------------------------

class TestLinkResponseFromRecord:
    """from_record must copy code, url, and clicks faithfully."""

    def test_from_record_maps_code(self):
        """SLI 3: response code equals record code."""
        r = LinkRecord(code="abc123", url="https://example.com", clicks=0)
        assert LinkResponse.from_record(r).code == "abc123"

    def test_from_record_maps_url(self):
        """SLI 3: response url equals record url byte-for-byte."""
        r = LinkRecord(code="abc123", url="https://example.com/exact", clicks=0)
        assert LinkResponse.from_record(r).url == "https://example.com/exact"

    def test_from_record_maps_clicks(self):
        """SLI 5: response clicks equals record clicks."""
        r = LinkRecord(code="abc123", url="https://example.com", clicks=7)
        assert LinkResponse.from_record(r).clicks == 7

    def test_from_record_zero_clicks(self):
        """SLI 5: newly created record maps to clicks == 0."""
        r = LinkRecord(code="abc123", url="https://example.com")
        assert LinkResponse.from_record(r).clicks == 0


# ---------------------------------------------------------------------------
# SLI 4 — create validation: CreateLinkRequest
# ---------------------------------------------------------------------------

class TestCreateLinkRequestCurrentBehaviour:
    """Document what the schema accepts TODAY (no validation yet).

    These tests are intentionally descriptive, not prescriptive — they will
    break when URL validation (finding #2) is implemented, at which point they
    should be replaced by the prescriptive tests in the placeholder below.
    """

    def test_accepts_valid_https_url(self):
        """A well-formed https URL must always be accepted."""
        req = CreateLinkRequest(url="https://example.com/path")
        assert req.url == "https://example.com/path"

    def test_accepts_valid_http_url(self):
        req = CreateLinkRequest(url="http://example.com")
        assert req.url == "http://example.com"

    def test_url_field_is_required(self):
        """SLI 4: omitting url must raise a validation error."""
        with pytest.raises(ValidationError):
            CreateLinkRequest()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# SLI 4 — placeholder for post-finding-#2 validation tests
# ---------------------------------------------------------------------------
# Once CreateLinkRequest (or create_link) gains URL validation, add:
#
#   def test_rejects_javascript_scheme(self): ...   # open-redirect / XSS
#   def test_rejects_data_scheme(self): ...
#   def test_rejects_empty_string(self): ...        # empty Location → self-redirect loop
#   def test_rejects_bare_word(self): ...           # relative path on redirect
#   def test_rejects_file_scheme(self): ...
#   def test_accepts_https_with_path_and_query(self): ...
