from pyrateyourmusic._clean import (
    artist_slug_from_url,
    clean,
    parse_count,
    parse_rating,
    parse_year,
    release_slug_from_url,
    release_type_from_url,
)


class TestParseCount:
    def test_compact_k(self):
        assert parse_count("106k") == 106000

    def test_decimal_k(self):
        assert parse_count("1.2k") == 1200

    def test_compact_m(self):
        assert parse_count("2m") == 2000000

    def test_comma(self):
        assert parse_count("49,576") == 49576

    def test_plain(self):
        assert parse_count("694") == 694

    def test_empty(self):
        assert parse_count("") is None


class TestParseRating:
    def test_bare(self):
        assert parse_rating("4.38") == 4.38

    def test_with_max(self):
        assert parse_rating("4.38 / 5") == 4.38

    def test_none(self):
        assert parse_rating("n/a") is None


class TestParseYear:
    def test_from_date(self):
        assert parse_year("15 March 2015") == 2015

    def test_none(self):
        assert parse_year("no date") is None


class TestSlugs:
    def test_release_slug(self):
        assert release_slug_from_url(
            "https://rateyourmusic.com/release/album/radiohead/ok-computer/"
        ) == "radiohead/ok-computer"

    def test_release_type(self):
        assert release_type_from_url(
            "https://rateyourmusic.com/release/ep/foo/bar/"
        ) == "ep"

    def test_artist_slug(self):
        assert artist_slug_from_url("/artist/radiohead") == "radiohead"

    def test_non_release(self):
        assert release_slug_from_url("/artist/radiohead") == ""


def test_clean_collapses_whitespace():
    assert clean("  a\n  b\t c ") == "a b c"
