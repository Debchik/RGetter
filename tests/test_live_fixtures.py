"""Offline tests against live-captured fixture HTML.

These tests parse real RYM pages that were captured while the live probe
ran, giving coverage of the actual current markup without requiring a
network connection at test time.

Fixtures are captured by running the library against a live FlareSolverr
endpoint and saving the HTML to tests/fixtures/. They are committed to the
repo so CI can run them offline.
"""
from __future__ import annotations

from pyrateyourmusic._parse import parse_artist_page, parse_chart, parse_release_page


class TestLiveChartFixture:
    def test_parses_multiple_rows(self, chart_live_html):
        rows = parse_chart(chart_live_html)
        assert len(rows) >= 20

    def test_first_row_fields(self, chart_live_html):
        row = parse_chart(chart_live_html)[0]
        assert row["rym_id"]
        assert row["title"]
        assert row["artist"]
        assert row["artist_id"]
        assert row["year"] is not None
        assert row["rating"] is not None
        assert row["n_ratings"] and row["n_ratings"] > 0
        assert row["primary_genres"]

    def test_rows_have_urls(self, chart_live_html):
        rows = parse_chart(chart_live_html)
        for row in rows:
            assert row["url"].startswith("https://rateyourmusic.com/release/")

    def test_known_top_entry(self, chart_live_html):
        rows = parse_chart(chart_live_html)
        rym_ids = [r["rym_id"] for r in rows]
        # Kendrick Lamar - To Pimp a Butterfly is the long-standing #1
        assert "kendrick-lamar/to-pimp-a-butterfly" in rym_ids
        tptb = next(r for r in rows if r["rym_id"] == "kendrick-lamar/to-pimp-a-butterfly")
        assert tptb["rating"] >= 4.0
        assert "Conscious Hip Hop" in tptb["primary_genres"]


class TestLiveArtistFixture:
    def test_name_and_slug(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        assert a["name"] == "Radiohead"
        assert a["rym_id"] == "radiohead"

    def test_formed_populated(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        assert "1991" in a["formed"]

    def test_members_no_roles(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        assert "Thom Yorke" in a["members"]
        assert "Jonny Greenwood" in a["members"]
        assert all("(" not in m for m in a["members"])

    def test_genres(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        assert "Alternative Rock" in a["genres"]

    def test_discography_rich(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        assert len(a["discography"]) >= 8
        ids = [d["rym_id"] for d in a["discography"]]
        assert "radiohead/ok-computer" in ids

    def test_discography_has_ratings(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        rated = [d for d in a["discography"] if d["rating"] is not None]
        assert len(rated) >= 5

    def test_discography_has_years(self, artist_live_html):
        a = parse_artist_page(artist_live_html, "radiohead")
        pablo = next((d for d in a["discography"] if "pablo-honey" in d["rym_id"]), None)
        assert pablo is not None
        assert pablo["year"] == 1993


class TestWaybackReleaseFixture:
    """Tests using a Wayback Machine snapshot of a release detail page.

    Wayback snapshots reliably carry title, artist, tracklist, rating and
    cover; genres/descriptors may be absent in older snapshots.
    """

    def test_basics(self, release_wayback_html):
        r = parse_release_page(release_wayback_html, "radiohead/ok-computer")
        assert r["title"] == "OK Computer"
        assert r["artist"] == "Radiohead"
        assert r["rym_id"] == "radiohead/ok-computer"

    def test_rating(self, release_wayback_html):
        r = parse_release_page(release_wayback_html, "radiohead/ok-computer")
        assert r["rating"] is not None
        assert 3.5 <= r["rating"] <= 5.0

    def test_n_ratings(self, release_wayback_html):
        r = parse_release_page(release_wayback_html, "radiohead/ok-computer")
        assert r["n_ratings"] is not None
        assert r["n_ratings"] > 10000

    def test_tracklist_populated(self, release_wayback_html):
        r = parse_release_page(release_wayback_html, "radiohead/ok-computer")
        assert len(r["tracklist"]) >= 10

    def test_cover_url(self, release_wayback_html):
        r = parse_release_page(release_wayback_html, "radiohead/ok-computer")
        assert r["cover_url"].startswith("https://")

    def test_artist_id(self, release_wayback_html):
        r = parse_release_page(release_wayback_html, "radiohead/ok-computer")
        assert r["artist_id"] == "radiohead"


class TestGetReleaseWaybackFallback:
    """Unit test the fallback chain in get_release without network."""

    def test_wayback_used_on_503(self, monkeypatch, release_wayback_html):
        """When live fetch raises RuntimeError, Wayback is tried."""
        import pyrateyourmusic.release as rel_mod

        def mock_get_html(path, **kwargs):
            raise RuntimeError("503 origin block (mocked)")

        def mock_wayback_html(url):
            return release_wayback_html

        monkeypatch.setattr(rel_mod, "get_html", mock_get_html)

        import importlib
        import types

        # patch unblock_requests.wayback_html inside the module namespace
        fake_ub = types.SimpleNamespace(wayback_html=mock_wayback_html)
        monkeypatch.setitem(__builtins__ if isinstance(__builtins__, dict) else vars(__builtins__), "_", None)

        # Use the direct import path the module uses
        import sys
        import unblock_requests as ub_real
        original = ub_real.wayback_html
        try:
            ub_real.wayback_html = mock_wayback_html
            release = rel_mod.get_release("radiohead/ok-computer")
            assert release.title == "OK Computer"
            assert release.artist == "Radiohead"
        finally:
            ub_real.wayback_html = original

    def test_raises_when_both_fail(self, monkeypatch):
        """RuntimeError is raised with clear guidance when live + Wayback both fail."""
        import pyrateyourmusic.release as rel_mod
        import unblock_requests as ub_real

        def mock_get_html(path, **kwargs):
            raise RuntimeError("503 origin block (mocked)")

        def mock_wayback_html(url):
            raise ConnectionError("wayback unavailable (mocked)")

        monkeypatch.setattr(rel_mod, "get_html", mock_get_html)
        original = ub_real.wayback_html
        try:
            ub_real.wayback_html = mock_wayback_html
            import pytest
            with pytest.raises(RuntimeError, match="503 origin block"):
                rel_mod.get_release("radiohead/ok-computer")
        finally:
            ub_real.wayback_html = original
