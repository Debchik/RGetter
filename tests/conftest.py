import os

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def chart_html() -> str:
    return _read("chart.html")


@pytest.fixture
def artist_html() -> str:
    return _read("artist.html")


@pytest.fixture
def release_html() -> str:
    return _read("release.html")
