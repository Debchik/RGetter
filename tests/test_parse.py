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
