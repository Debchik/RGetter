from pyrateyourmusic._parse import (
    parse_artist_page,
    parse_chart,
    parse_release_page,
)


class TestParseChart:
    def test_row_count(self, chart_html):
        rows = parse_chart(chart_html)
        assert len(rows) == 3

    def test_first_row(self, chart_html):
        row = parse_chart(chart_html)[0]
        assert row["rym_id"] == "kendrick-lamar/to-pimp-a-butterfly"
        assert row["title"] == "To Pimp a Butterfly"
        assert row["artist"] == "Kendrick Lamar"
        assert row["artist_id"] == "kendrick-lamar"
        assert row["year"] == 2015
        assert row["rating"] == 4.38
        assert row["n_ratings"] == 106000
        assert row["release_type"] == "album"
        assert row["position"] == 1

    def test_genres(self, chart_html):
        row = parse_chart(chart_html)[0]
        assert "Conscious Hip Hop" in row["primary_genres"]
        assert "Neo-Soul" in row["secondary_genres"]

    def test_url_absolute(self, chart_html):
        row = parse_chart(chart_html)[0]
        assert row["url"].startswith("https://rateyourmusic.com/release/")


class TestParseArtist:
    def test_name(self, artist_html):
        a = parse_artist_page(artist_html, "radiohead")
        assert a["name"] == "Radiohead"
        assert a["rym_id"] == "radiohead"

    def test_formed(self, artist_html):
        a = parse_artist_page(artist_html, "radiohead")
        assert "1991" in a["formed"]

    def test_members(self, artist_html):
        a = parse_artist_page(artist_html, "radiohead")
        assert "Thom Yorke" in a["members"]
        # instrument roles must not split into extra members
        assert all("(" not in m for m in a["members"])

    def test_aliases_include_unlinked(self, artist_html):
        a = parse_artist_page(artist_html, "radiohead")
        assert "On a Friday" in a["aliases"]
        assert "Shindig" in a["aliases"]

    def test_genres(self, artist_html):
        a = parse_artist_page(artist_html, "radiohead")
        assert "Alternative Rock" in a["genres"]

    def test_discography(self, artist_html):
        a = parse_artist_page(artist_html, "radiohead")
        ids = [d["rym_id"] for d in a["discography"]]
        assert "radiohead/pablo-honey" in ids
        first = a["discography"][0]
        assert first["year"] == 1993
        assert first["rating"] is not None
        assert first["n_ratings"] is not None

    def test_discography_artist_id(self, artist_html):
        # Regression: discography rows must carry the *artist's* slug, not
        # the release-title slug (artist_slug_from_url was being called with
        # the release URL, whose last path segment is the title, not the
        # artist).
        a = parse_artist_page(artist_html, "radiohead")
        assert a["discography"]
        for d in a["discography"]:
            assert d["artist_id"] == "radiohead"


class TestParseRelease:
    def test_basics(self, release_html):
        r = parse_release_page(release_html, "radiohead/ok-computer")
        assert r["title"] == "OK Computer"
        assert r["artist"] == "Radiohead"
        assert r["artist_id"] == "radiohead"
        assert r["release_type"] == "album"
        assert r["year"] == 1997
        assert r["rating"] == 4.23
        assert r["n_ratings"] == 136046

    def test_genres_and_descriptors(self, release_html):
        r = parse_release_page(release_html, "radiohead/ok-computer")
        assert "Alternative Rock" in r["primary_genres"]
        assert "Post-Britpop" in r["secondary_genres"]
        assert "melancholic" in r["descriptors"]

    def test_tracklist(self, release_html):
        r = parse_release_page(release_html, "radiohead/ok-computer")
        assert len(r["tracklist"]) == 3
        pos, title, dur = r["tracklist"][1]
        assert title == "Paranoid Android"
        assert dur == "6:23"


def test_release_title_beginning_with_by():
    """The word By is not a reliable separator between title and artist."""
    html = """<div class="album_title">By the Way
              <span class="album_artist_small">By
                <a class="artist" href="/artist/example">Example</a>
              </span></div>"""
    release = parse_release_page(html, "example/by-the-way")
    assert release["title"] == "By the Way"


def test_release_type_preserved_when_info_table_missing():
    html = """<div class="album_title">Test EP
              <span class="album_artist_small">By
                <a class="artist" href="/artist/example">Example</a>
              </span></div>"""
    release = parse_release_page(html, "example/test-ep", release_type="ep")
    assert release["release_type"] == "ep"
    assert "/release/ep/" in release["url"]


def test_realistic_rym_single_tracklist_not_duplicated():
    """Real RYM <li class=track> wraps a nested .tracklist_line."""
    html = """<div class="album_title">Yung Hefner
                <span class="album_artist_small">By <a class="artist" href="/artist/morgenshtern">Morgenshtern</a></span>
              </div>
              <ul id="tracks"><li class="track">
                <div class="tracklist_line">
                  <span class="tracklist_num">1</span>
                  <span class="tracklist_title">
                    <span><a class="song" href="/song/morgenshtern/yung-hefner/">Yung Hefner</a>
                    <a class="tracks_lyric_link">lyrics</a>
                    <span class="tracklist_duration">2:15</span></span>
                  </span>
                </div>
              </li></ul>"""
    result = parse_release_page(html, "morgenshtern/yung-hefner", release_type="single")
    assert len(result["tracklist"]) == 1
    assert result["tracklist"][0] == ("1", "Yung Hefner", "2:15")
