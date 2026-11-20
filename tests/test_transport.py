"""Network transport unit tests; no real requests are made."""
from unittest.mock import Mock

import pytest

from pyrateyourmusic import transport


def test_real_http_503_triggers_runtime_error(monkeypatch):
    response = Mock()
    response.status_code = 503
    response.text = "Service Unavailable"
    response.raise_for_status.side_effect = AssertionError(
        "raise_for_status should not run before handling 503"
    )
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(transport, "get_session", lambda: session)
    monkeypatch.setattr(transport, "_throttle", lambda: None)
    with pytest.raises(RuntimeError, match="503 origin block"):
        transport.get_html("/release/single/a/b/")


def test_successful_html_response(monkeypatch):
    response = Mock()
    response.status_code = 200
    response.text = "<html>ok</html>"
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(transport, "get_session", lambda: session)
    monkeypatch.setattr(transport, "_throttle", lambda: None)
    assert transport.get_html("/artist/a") == "<html>ok</html>"
    response.raise_for_status.assert_called_once()
