"""Offline track-first candidate generation; albums are not part of the input."""
import csv

import pytest

from pyrateyourmusic.matching import (
    connect, export_candidates, export_spotify_links, ingest_tracks, verify_html,
)


FIELDS = [
    "spotify_track_id", "spotify_track_name", "spotify_artist_id",
    "artist_name", "isrc", "duration_ms", "original_release_date",
]


def _input(tmp_path):
    source = tmp_path / "tracks_artists.csv"
    with source.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows([
            dict(spotify_track_id="spotify-t1", spotify_track_name="Yung Hefner",
                 spotify_artist_id="artist-m", artist_name="Morgenshtern", isrc="X1",
                 duration_ms="140000", original_release_date="2020-01-01"),
            dict(spotify_track_id="spotify-t1", spotify_track_name="Yung Hefner",
                 spotify_artist_id="artist-feat", artist_name="Another Artist", isrc="X1",
                 duration_ms="140000", original_release_date="2020-01-01"),
            dict(spotify_track_id="spotify-t2", spotify_track_name="Tidal",
                 spotify_artist_id="artist-mega", artist_name="mega:oba", isrc="X2",
                 duration_ms="180000", original_release_date=""),
            dict(spotify_track_id="spotify-t2", spotify_track_name="Tidal",
                 spotify_artist_id="artist-mega", artist_name="mega:oba", isrc="X2",
                 duration_ms="180000", original_release_date=""),
            dict(spotify_track_id="", spotify_track_name="Unknown",
                 spotify_artist_id="artist-mega", artist_name="mega:oba", isrc="",
                 duration_ms="", original_release_date=""),
        ])
    return source


def test_track_first_no_album_fields_or_membership_claim(tmp_path):
    source, db = _input(tmp_path), tmp_path / "matches.sqlite"
    result = ingest_tracks(source, db, batch_size=2)
    assert result["rows_read"] == 5
    assert result["eligible_rows"] == 4
    assert result["skipped_rows"] == 1
    assert result["distinct_spotify_tracks"] == 2
    assert result["distinct_track_artist_pairs"] == 3
    assert result["unique_entities"] == 6
    assert ingest_tracks(source, db)["distinct_track_artist_pairs"] == 3

    with connect(db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM spotify_tracks WHERE spotify_single_id = ''"
        ).fetchone()[0] == 3
        assert {r[0] for r in connection.execute(
            "SELECT DISTINCT spotify_join_method FROM spotify_tracks"
        )} == {"track_artist_id_join"}
        assert {r[0] for r in connection.execute(
            "SELECT DISTINCT kind FROM entities"
        )} == {"song", "single"}

    urls_file = tmp_path / "candidates.csv"
    export_candidates(db, urls_file)
    url_text = urls_file.read_text(encoding="utf-8")
    assert "https://rateyourmusic.com/song/morgenshtern/yung-hefner/" in url_text
    assert "https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/" in url_text
    assert "mega_oba/tidal/" in url_text

    relations_file = tmp_path / "source_links.csv"
    assert export_spotify_links(db, relations_file) > 0
    with relations_file.open(newline="", encoding="utf-8") as fh:
        relations = list(csv.DictReader(fh))
    assert all(r["spotify_single_id"] == "" for r in relations)
    assert all(r["spotify_join_method"] == "track_artist_id_join" for r in relations)


def test_song_only_and_resume_with_single_candidates(tmp_path):
    db = tmp_path / "matches.sqlite"
    source = _input(tmp_path)
    ingest_tracks(source, db, kinds=("song",))
    with connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM entities").fetchone()[0] == 3
        assert connection.execute(
            "SELECT count(*) FROM entities WHERE kind='single'"
        ).fetchone()[0] == 0
    ingest_tracks(source, db, kinds=("single",))
    with connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM entities").fetchone()[0] == 6


def test_invalid_schema_and_kinds(tmp_path):
    source = tmp_path / "broken.csv"
    source.write_text("spotify_track_id,artist_name\nx,A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing columns"):
        ingest_tracks(source, tmp_path / "db.sqlite")
    with pytest.raises(ValueError, match="kinds"):
        ingest_tracks(source, tmp_path / "db.sqlite", kinds=("album",))


def test_can_verify_guessed_url_without_spotify_album(tmp_path):
    db = tmp_path / "matches.sqlite"
    ingest_tracks(_input(tmp_path), db)
    url = "https://rateyourmusic.com/song/morgenshtern/yung-hefner/"
    html = """<meta property="og:url"
                    content="https://rateyourmusic.com/song/morgenshtern/yung-hefner/">
              <div id="page_song_temp_section_header"><h1>Yung Hefner</h1></div>
              <div class="page_song_header_info_artist">
                <a class="artist">Morgenshtern</a>
              </div>"""
    assert verify_html(db, url, html)["verified"] == 1
