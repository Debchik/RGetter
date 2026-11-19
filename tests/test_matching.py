"""Tests for the Spotify singles matching pipeline (no live network)."""
import csv

import pytest

from pyrateyourmusic.matching import (
    export_candidates, ingest_singles, page_identity, slug_variants,
    urls_for, verify_html,
)


def _csv(tmp_path):
    path = tmp_path / "joined.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "spotify_track_id", "spotify_track_name", "spotify_single_id",
            "single_name", "spotify_artist_id", "artist_name", "album_type",
            "total_tracks", "isrc",
        ])
        writer.writeheader()
        for track_id, name, a_type, n in [
            ("1", "Yung Hefner", "single", "1"),
            ("2", "Other", "single", "2"),
            ("1", "Yung Hefner", "single", "1"),
            ("3", "Wrong type", "album", "1"),
        ]:
            writer.writerow(dict(spotify_track_id=track_id, spotify_track_name=name,
                                 spotify_single_id="A", single_name="Yung Hefner",
                                 spotify_artist_id="X", artist_name="Morgenshtern",
                                 album_type=a_type, total_tracks=n, isrc=""))
    return path


def test_url_guesses():
    assert "mega_oba" in slug_variants("mega:oba")
    assert "https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/" in urls_for(
        "single", "Morgenshtern", "Yung Hefner")
    assert len(urls_for("song", "mega:oba", "Tidal")) <= 8
    with pytest.raises(ValueError):
        urls_for("album", "A", "B")


def test_filter_dedup_and_resume(tmp_path):
    source, db = _csv(tmp_path), tmp_path / "matches.sqlite"
    result = ingest_singles(source, db, batch_size=2)
    assert result["rows_read"] == 4
    assert result["eligible_rows"] == 2
    assert result["unique_tracks"] == 1
    assert result["unique_entities"] == 2
    assert ingest_singles(source, db)["unique_tracks"] == 1
    target = tmp_path / "urls.csv"
    assert export_candidates(db, target) > 0
    assert "unverified" in target.read_text()


def test_missing_join_columns_fail_closed(tmp_path):
    source = tmp_path / "invalid.csv"
    source.write_text("spotify_track_id,artist_name\n1,A\n")
    with pytest.raises(ValueError, match="Missing columns"):
        ingest_singles(source, tmp_path / "db.sqlite")


def test_verify_html_checks_canonical_artist_title(tmp_path):
    db = tmp_path / "db.sqlite"
    ingest_singles(_csv(tmp_path), db)
    url = "https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/"
    assert verify_html(db, url, "<title>HTTP ERROR 503</title>")["verified"] == 0
    html = ("""<meta property="og:url" content="https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/"/>
    <div class="album_title">Yung Hefner <div class="album_artist_small">By
    <a class="artist">Morgenshtern</a></div></div>""")
    report = verify_html(db, url, html)
    assert report["verified"] == 1
    assert page_identity(html)[3] == "Yung Hefner"


def test_reject_wrong_song_identity(tmp_path):
    db = tmp_path / "db.sqlite"
    ingest_singles(_csv(tmp_path), db)
    url = "https://rateyourmusic.com/song/morgenshtern/yung-hefner/"
    html = ("""<meta property="og:url" content="https://rateyourmusic.com/song/morgenshtern/yung-hefner/"/>
    <div id="page_song_temp_section_header"><h1>Another Song</h1></div>
    <h2 class="page_song_header_info_artist"><a class="artist">Morgenshtern</a></h2>""")
    assert verify_html(db, url, html)["verified"] == 0
