import os

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def _fixture_exists(name: str) -> bool:
    return os.path.exists(os.path.join(FIXTURES, name))


@pytest.fixture
def chart_html() -> str:
    return _read("chart.html")


@pytest.fixture
def artist_html() -> str:
    return _read("artist.html")


@pytest.fixture
def release_html() -> str:
    return _read("release.html")


# Live-captured fixtures (large real pages; skipped when absent)

@pytest.fixture
def chart_live_html():
    if not _fixture_exists("chart_live.html"):
        pytest.skip("chart_live.html not captured yet")
    return _read("chart_live.html")


@pytest.fixture
def artist_live_html():
    if not _fixture_exists("artist_live.html"):
        pytest.skip("artist_live.html not captured yet")
    return _read("artist_live.html")


@pytest.fixture
def release_wayback_html():
    if not _fixture_exists("release_wayback.html"):
        pytest.skip("release_wayback.html not captured yet")
    return _read("release_wayback.html")
