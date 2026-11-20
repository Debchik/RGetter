"""Offline Spotify single -> RateYourMusic candidate generation and HTML verification.

No network calls. Candidate URLs are hypotheses, never confirmed matches.
The caller is responsible for obtaining RYM HTML through an authorized channel.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlparse, urljoin

from bs4 import BeautifulSoup

RYM = "https://rateyourmusic.com"
REQUIRED = {
    "spotify_track_id", "spotify_track_name", "spotify_single_id",
    "single_name", "spotify_artist_id", "artist_name", "album_type", "total_tracks",
}


def identity(value: str) -> str:
    """Conservative matching key: preserve punctuation to prevent collisions."""
    value = unicodedata.normalize("NFKC", value).casefold().replace("’", "'")
    return re.sub(r"\s+", " ", value).strip()


def slug_variants(value: str) -> list[str]:
    """Small bounded set of guessed slugs. None are asserted canonical."""
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.replace("&", " and ").replace("’", "").replace("'", "")
    variants = []
    # RYM punctuation differs across artist and song pages (mega:oba -> mega_oba).
    for sep in ("-", "_"):
        candidate = re.sub(r"[^\w\s-]+", sep, value)
        candidate = re.sub(r"[\s_-]+", sep, candidate).strip("-_ ")
        if candidate and candidate not in variants:
            variants.append(candidate)
    # Preserve existing underscores, which sometimes occur in canonical artist URLs.
    candidate = re.sub(r"[^\w\s-]+", "-", value)
    candidate = re.sub(r"[\s-]+", "-", candidate).strip("-_ ")
    if candidate and candidate not in variants:
        variants.append(candidate)
    return [quote(s, safe="-_") for s in variants[:3]]


def urls_for(kind: str, artist: str, title: str, max_urls: int = 8) -> list[str]:
    """Propose bounded URLs for song or single. No requests are performed."""
    if kind not in ("song", "single"):
        raise ValueError("Only song and single are supported")
    prefix = "/song/" if kind == "song" else "/release/single/"
    out = []
    for a in slug_variants(artist):
        for t in slug_variants(title):
            url = f"{RYM}{prefix}{a}/{t}/"
            if url not in out:
                out.append(url)
            if len(out) >= max_urls:
                return out
    return out


def _entity_key(kind: str, artist: str, title: str) -> str:
    payload = "\x1f".join((kind, identity(artist), identity(title)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(path))
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS spotify_tracks (
        spotify_track_id TEXT NOT NULL, spotify_single_id TEXT NOT NULL,
        spotify_artist_id TEXT NOT NULL, track_name TEXT NOT NULL,
        single_name TEXT NOT NULL, artist_name TEXT NOT NULL,
        release_date TEXT, duration_ms TEXT, isrc TEXT,
        spotify_join_method TEXT NOT NULL DEFAULT 'unspecified',
        PRIMARY KEY (spotify_track_id, spotify_single_id, spotify_artist_id)
    );
    CREATE TABLE IF NOT EXISTS entities (
        entity_key TEXT PRIMARY KEY, kind TEXT NOT NULL,
        artist_name TEXT NOT NULL, title TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS links (
        spotify_track_id TEXT NOT NULL, spotify_single_id TEXT NOT NULL,
        spotify_artist_id TEXT NOT NULL, entity_key TEXT NOT NULL,
        PRIMARY KEY (spotify_track_id, spotify_single_id, spotify_artist_id, entity_key)
    );
    CREATE TABLE IF NOT EXISTS candidates (
        entity_key TEXT NOT NULL, url TEXT NOT NULL, rank INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'unverified',
        observed_artist TEXT, observed_title TEXT,
        PRIMARY KEY (entity_key, url)
    );
    CREATE INDEX IF NOT EXISTS candidates_by_url ON candidates(url);
    CREATE INDEX IF NOT EXISTS links_by_entity ON links(entity_key);
    """)
    # Existing databases created by earlier versions remain readable.
    columns = {row[1] for row in db.execute("PRAGMA table_info(spotify_tracks)")}
    if "spotify_join_method" not in columns:
        db.execute(
            "ALTER TABLE spotify_tracks "
            "ADD COLUMN spotify_join_method TEXT NOT NULL DEFAULT 'unspecified'"
        )
        db.commit()
    return db


def _insert_entity(db: sqlite3.Connection, row: dict, kind: str, title: str) -> None:
    artist = row["artist_name"].strip()
    key = _entity_key(kind, artist, title)
    created = db.execute(
        "INSERT OR IGNORE INTO entities VALUES (?, ?, ?, ?)",
        (key, kind, artist, title),
    ).rowcount
    db.execute(
        "INSERT OR IGNORE INTO links VALUES (?, ?, ?, ?)",
        (row["spotify_track_id"], row["spotify_single_id"],
         row["spotify_artist_id"], key),
    )
    if created:
        db.executemany(
            "INSERT OR IGNORE INTO candidates(entity_key,url,rank) VALUES (?,?,?)",
            ((key, u, rank) for rank, u in enumerate(urls_for(kind, artist, title), 1)),
        )


def ingest_singles(input_csv: str | Path, sqlite_path: str | Path,
                   batch_size: int = 2000, limit: int | None = None) -> dict:
    """Stream a pre-joined CSV; enforce single/one-track filter again for safety."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    db = connect(sqlite_path)
    rows = eligible = skipped = 0
    try:
        with open(input_csv, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            missing = REQUIRED - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
            for row in reader:
                if limit is not None and rows >= limit:
                    break
                rows += 1
                if (row["album_type"].strip().lower() != "single"
                        or row["total_tracks"].strip() != "1"):
                    skipped += 1
                    continue
                if any(not row[k].strip() for k in REQUIRED - {"album_type", "total_tracks"}):
                    skipped += 1
                    continue
                eligible += 1
                db.execute(
                    """INSERT OR IGNORE INTO spotify_tracks
                       (spotify_track_id,spotify_single_id,spotify_artist_id,
                        track_name,single_name,artist_name,release_date,
                        duration_ms,isrc,spotify_join_method)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (row["spotify_track_id"], row["spotify_single_id"],
                     row["spotify_artist_id"], row["spotify_track_name"],
                     row["single_name"], row["artist_name"],
                     row.get("release_date") or "", row.get("duration_ms") or "",
                     row.get("isrc") or "",
                     (row.get("spotify_join_method") or "unspecified").strip()),
                )
                _insert_entity(db, row, "single", row["single_name"].strip())
                _insert_entity(db, row, "song", row["spotify_track_name"].strip())
                if rows % batch_size == 0:
                    db.commit()
        db.commit()
        return {
            "rows_read": rows, "eligible_rows": eligible, "skipped_rows": skipped,
            "unique_tracks": db.execute("SELECT count(*) FROM spotify_tracks").fetchone()[0],
            "unique_entities": db.execute("SELECT count(*) FROM entities").fetchone()[0],
            "candidate_relations": db.execute("SELECT count(*) FROM candidates").fetchone()[0],
            "unique_urls": db.execute("SELECT count(DISTINCT url) FROM candidates").fetchone()[0],
        }
    finally:
        db.close()


def export_candidates(sqlite_path: str | Path, output_csv: str | Path) -> int:
    """Export URL hypotheses; multiple Spotify entities can map to one URL."""
    db = connect(sqlite_path)
    count = 0
    try:
        with open(output_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["url", "kind", "artist_name", "title", "status", "rank"])
            for row in db.execute("""
                    SELECT c.url,e.kind,e.artist_name,e.title,c.status,c.rank
                    FROM candidates c JOIN entities e USING (entity_key)
                    ORDER BY c.url, c.rank"""):
                writer.writerow(row)
                count += 1
    finally:
        db.close()
    return count


def export_spotify_links(sqlite_path: str | Path, output_csv: str | Path) -> int:
    """Export source Spotify IDs alongside candidate URLs and join provenance.

    Each row is one source track/release/artist link to one URL hypothesis.
    An unverified URL or a heuristic Spotify join is NOT ground truth.
    """
    db = connect(sqlite_path)
    count = 0
    try:
        with open(output_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([
                "spotify_track_id", "spotify_single_id", "spotify_artist_id",
                "spotify_join_method", "entity_kind", "candidate_url",
                "candidate_status", "candidate_rank",
            ])
            for record in db.execute("""
                SELECT l.spotify_track_id,l.spotify_single_id,
                       l.spotify_artist_id,s.spotify_join_method,e.kind,
                       c.url,c.status,c.rank
                FROM links l
                JOIN spotify_tracks s
                  ON s.spotify_track_id=l.spotify_track_id
                 AND s.spotify_single_id=l.spotify_single_id
                 AND s.spotify_artist_id=l.spotify_artist_id
                JOIN entities e ON e.entity_key=l.entity_key
                JOIN candidates c ON c.entity_key=l.entity_key
                ORDER BY l.spotify_track_id,l.spotify_single_id,c.rank
            """):
                writer.writerow(record)
                count += 1
    finally:
        db.close()
    return count


def _canonical(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname not in ("rateyourmusic.com", "www.rateyourmusic.com"):
        return ""
    return parsed.path.rstrip("/") + "/"


def page_identity(html: str) -> tuple[str, str, str, str]:
    """Return (canonical path, kind, artist, title); empty on unrelated pages."""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.select_one('meta[property="og:url"]')
    canonical = _canonical(str(meta.get("content") or "")) if meta else ""
    if canonical.startswith("/song/"):
        title_el = soup.select_one("#page_song_temp_section_header h1")
        artist_el = soup.select_one(".page_song_header_info_artist a.artist")
        return (canonical, "song",
                artist_el.get_text(" ", strip=True) if artist_el else "",
                title_el.get_text(" ", strip=True) if title_el else "")
    if canonical.startswith("/release/single/"):
        title_el = soup.select_one(".album_title")
        artist_el = soup.select_one(".album_artist_small a.artist, .album_info a.artist")
        direct = "".join(str(t) for t in title_el.find_all(string=True, recursive=False)) if title_el else ""
        return (canonical, "single",
                artist_el.get_text(" ", strip=True) if artist_el else "",
                direct.strip())
    return (canonical, "", "", "")



def song_links_in_single(html: str) -> list[str]:
    """Extract *actual* /song/ links from a saved single's tracklist.

    A linked song is evidence of a RYM relationship, not yet a verified
    match to any Spotify recording.
    """
    canonical, kind, _, _ = page_identity(html)
    if kind != "single" or not canonical.startswith("/release/single/"):
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for anchor in soup.select('#tracks a.song[href*="/song/"]'):
        url = urljoin(RYM + "/", str(anchor.get("href") or ""))
        if _canonical(url).startswith("/song/") and url not in urls:
            urls.append(url)
    return urls


def verify_html(sqlite_path: str | Path, url: str, html: str) -> dict:
    """Verify a saved page against candidate names and its canonical URL.

    No HTTP status or response body alone counts as a confirmed match.
    Only exact normalized artist+title matches qualify.
    """
    expected = _canonical(url)
    canonical, kind, artist, title = page_identity(html)
    # A blocked/error page is not evidence of a mismatch. Leave existing
    # verification statuses unchanged so retrying cannot erase confirmed data.
    if not canonical or not kind or not artist or not title:
        return {"url": url, "canonical_path": canonical, "kind": kind,
                "observed_artist": artist, "observed_title": title,
                "checked": 0, "verified": 0, "error": "unreadable_page"}
    db = connect(sqlite_path)
    updated = verified = 0
    try:
        for key, expected_kind, candidate_artist, candidate_title in db.execute("""
            SELECT c.entity_key,e.kind,e.artist_name,e.title
            FROM candidates c JOIN entities e USING(entity_key) WHERE c.url=?""", (url,)):
            good = (canonical == expected and kind == expected_kind
                    and bool(identity(artist)) and bool(identity(title))
                    and identity(artist) == identity(candidate_artist)
                    and identity(title) == identity(candidate_title))
            status = "verified" if good else "mismatch"
            db.execute("""UPDATE candidates SET status=?,observed_artist=?,observed_title=?
                          WHERE entity_key=? AND url=?""",
                       (status, artist, title, key, url))
            updated += 1
            verified += int(good)
        db.commit()
    finally:
        db.close()
    return {"url": url, "canonical_path": canonical, "kind": kind,
            "observed_artist": artist, "observed_title": title,
            "checked": updated, "verified": verified}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="CSV single-track Spotify singles -> SQLite")
    ingest.add_argument("csv")
    ingest.add_argument("sqlite")
    ingest.add_argument("--limit", type=int)
    export = sub.add_parser("export", help="Export unverified URL hypotheses")
    export.add_argument("sqlite")
    export.add_argument("csv")
    links_export = sub.add_parser(
        "export-links", help="Export Spotify IDs and join provenance for each URL hypothesis"
    )
    links_export.add_argument("sqlite")
    links_export.add_argument("csv")
    verify = sub.add_parser("verify-html", help="Validate one downloaded HTML file")
    verify.add_argument("sqlite")
    verify.add_argument("url")
    verify.add_argument("html")
    args = parser.parse_args()
    if args.command == "ingest":
        print(ingest_singles(args.csv, args.sqlite, limit=args.limit))
    elif args.command == "export":
        print(f"Exported {export_candidates(args.sqlite, args.csv)} candidate relations")
    elif args.command == "export-links":
        print(f"Exported {export_spotify_links(args.sqlite, args.csv)} Spotify candidate links")
    else:
        print(verify_html(args.sqlite, args.url, Path(args.html).read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
