"""Live smoke tests — require network + a FlareSolverr endpoint.

Run with ``pytest -m live``. Skipped automatically when
``PYRATEYOURMUSIC_FLARESOLVERR_URL`` is unset. Kept to a handful of page fetches
to stay polite against RYM's aggressive rate limiting.

Release detail pages 503 from datacenter IPs. The ``test_release_wayback_smoke``
test exercises the fallback chain: live fetch → Wayback Machine. It does NOT
assert live detail-page reachability; a Wayback result is accepted as success.
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


def test_release_wayback_smoke():
    """Exercises the live → Wayback fallback chain for release detail pages.

    From datacenter IPs the live fetch will 503; the test accepts a successful
    Wayback snapshot as passing. Only raises on total failure (both paths down).
    """
    from pyrateyourmusic import get_release, set_delay
    set_delay(3.0)
    r = get_release("radiohead/ok-computer")
    assert r.title == "OK Computer"
    assert r.artist == "Radiohead"
    assert r.rating is not None
    # tracklist comes through from Wayback snapshots
    assert r.track_count >= 10
