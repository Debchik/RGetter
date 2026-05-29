from pyrateyourmusic._parse import parse_artist_page, parse_chart, parse_release_page
from pyrateyourmusic.artist import _build_artist
from pyrateyourmusic.charts import _stubs_from_html
from pyrateyourmusic.models import Release, ReleaseStub, Track
from pyrateyourmusic.release import _build_release


def test_release_stub_from_chart(chart_html):
    stubs = _stubs_from_html(chart_html)
    assert isinstance(stubs[0], ReleaseStub)
    assert stubs[0].rym_id == "kendrick-lamar/to-pimp-a-butterfly"
    assert stubs[0].as_dict["rating"] == 4.38


def test_release_build(release_html):
    r = _build_release(release_html, "radiohead/ok-computer")
    assert isinstance(r, Release)
    assert r.track_count == 3
    assert isinstance(r.tracklist[0], Track)
    assert "Art Rock" in r.genres
    assert str(r) == "Radiohead - OK Computer (1997)"


def test_release_genres_dedup():
    r = Release(
        rym_id="a/b", title="B", artist="A", url="",
        primary_genres=["Rock", "Pop"], secondary_genres=["Pop", "Jazz"],
    )
    assert r.genres == ["Rock", "Pop", "Jazz"]


def test_artist_build(artist_html):
    a = _build_artist(artist_html, "radiohead")
    assert a.name == "Radiohead"
    assert a.release_count == len(a.discography)
    assert all(isinstance(s, ReleaseStub) for s in a.discography)
    d = a.as_dict
    assert d["rym_id"] == "radiohead"
    assert isinstance(d["discography"], list)
