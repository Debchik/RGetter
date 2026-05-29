"""Live smoke tests — require network + a FlareSolverr endpoint.

Run with ``pytest -m live``. Skipped automatically when
``PYRATEYOURMUSIC_FLARESOLVERR_URL`` is unset. Kept to 1-2 page fetches to stay
polite against RYM's aggressive rate limiting; release *detail* pages are not
exercised because they 503 from datacenter IPs.
"""
import pytest

from pyrateyourmusic.transport import flaresolverr_url

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not flaresolverr_url(),
        reason="set PYRATEYOURMUSIC_FLARESOLVERR_URL to run live tests",
    ),
]


def test_chart_smoke():
    from pyrateyourmusic import set_delay, top_albums
    set_delay(3.0)
    stubs = top_albums("all-time")
    assert len(stubs) > 10
    top = stubs[0]
    assert top.rym_id
    assert top.title
    assert top.artist
    assert top.rating is not None
    assert top.n_ratings and top.n_ratings > 0
    assert top.primary_genres


def test_artist_smoke():
    from pyrateyourmusic import get_artist, set_delay
    set_delay(3.0)
    a = get_artist("radiohead")
    assert a.name == "Radiohead"
    assert a.genres
    assert a.release_count > 5
    assert any(d.rym_id == "radiohead/ok-computer" for d in a.discography)
