# Spotify one-track singles → RateYourMusic candidate matching

This workflow is **offline by default**. It generates URL hypotheses and can
verify externally obtained HTML. It does not automatically crawl RYM or claim
that a generated link corresponds to a Spotify recording.

## Input: a *joined* CSV (not four independent LIMIT 100 samples)

Export one row per Spotify track + single + credited artist. Required columns:

| Column | Source | Meaning |
|---|---|---|
| `spotify_track_id` | tracks.`id` | Stable Spotify track identifier |
| `spotify_track_name` | tracks.`name` | Track name |
| `spotify_single_id` | albums.`id` | Stable Spotify release identifier |
| `single_name` | albums.`name` | Single name |
| `spotify_artist_id` | artists.`id` | Stable Spotify artist identifier |
| `artist_name` | artists.`name` | Artist name |
| `album_type` | albums.`album_type` | Must equal `single` |
| `total_tracks` | albums.`total_tracks` | Must equal `1` |
| `release_date` | albums.`release_date` | Optional |
| `duration_ms` | tracks | Optional for future disambiguation |
| `isrc` | tracks | Optional for future cross-linking |

**Key rule:** `rowid` columns are *local database keys*, whereas `id`
columns are external Spotify IDs. In the uploaded examples,
`artist_albums.album_rowid = albums.rowid` and
`artist_albums.artist_rowid = artists.rowid`.

The supplied examples do not yet expose the track↔album foreign key. Do not
assume a `tracks.album_rowid` exists without inspecting the real table schema.

A reliable export must begin with the complete related tables, not separate
`LIMIT 100` extracts: otherwise their foreign key ranges need not intersect.

### Verified portion of SQL: single–artist association

This query uses only column names **observed** in the supplied examples:

```sql
SELECT
  al.rowid      AS single_rowid,
  al.id         AS spotify_single_id,
  al.name       AS single_name,
  al.album_type,
  al.total_tracks,
  al.release_date,
  aa.artist_rowid,
  ar.id         AS spotify_artist_id,
  ar.name       AS artist_name
FROM albums AS al
JOIN artist_albums AS aa ON aa.album_rowid = al.rowid
JOIN artists AS ar ON ar.rowid = aa.artist_rowid
WHERE al.album_type = 'single'
  AND CAST(al.total_tracks AS INTEGER) = 1
  AND COALESCE(aa.is_appears_on, 0) = 0
  AND COALESCE(aa.is_implicit_appears_on, 0) = 0;
```

Use the *actual* foreign key from your tracks table (or its association table)
to attach `spotify_track_id` and `spotify_track_name`. If the track table is
already intersected with the target population of 20M tracks, make **that**
table the inner join. Do not infer that a release's name is automatically the
track name. Validate that exactly one desired track is linked to each selected
one-track release.

For multiple credited artists, export multiple rows; the matcher deduplicates
matching entities on disk. `index_in_album` may help establish credit order,
but do not silently discard collaborators until its semantics are validated.

## Run

```bash
pip install -e '.[test]'
python -m pyrateyourmusic.matching ingest joined_singles.csv matches.sqlite
python -m pyrateyourmusic.matching export matches.sqlite candidate_urls.csv
```

The CSV contains **unverified candidates**. Both URL families are generated:
`/release/single/<artist>/<single>/` and `/song/<artist>/<track>/`.
A limited number of punctuation variants is tried, including
`mega:oba → mega_oba`. These transformations are heuristics, not a
guarantee of canonical RYM slugs.

For authorized or pre-saved HTML, verify a candidate explicitly:

```bash
python -m pyrateyourmusic.matching verify-html matches.sqlite \
  https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/ \
  saved_single.html
```

The verifier requires an RYM `og:url` canonical path matching the candidate
and matching **both** artist and title from the page itself. A HTTP 200 page,
captcha, 503 body, redirect to another release, or similar title is **not** a
verified match.

From a saved RYM single page, `song_links_in_single(html)` extracts actual
`/song/` links in its tracklist. Those are observed RYM relationships, not
automatically verified matches to Spotify records.

## Scale and limitations

- SQLite deduplicates entities, source rows and candidate associations on disk.
  Re-running `ingest` is idempotent for the same inputs.
- Validate candidate precision on a labelled sample **before** any production
  lookups. Count unique URL targets, not input rows, for capacity planning.
- Source changes are not automatically reflected by `INSERT OR IGNORE`: use
  a fresh DB for a new snapshot, or add an explicit update/reconciliation stage.
- Only song and single candidate kinds are supported in this workflow.
- The original scraper's `artist`, `chart`, `release` methods remain
  available; no mass live crawler was added.
- RYM automated access is subject to its terms and any required permissions.
  The library does not provide authorization to scrape 20M items.

## Suggested validation before running large datasets

Count: input rows, unique track IDs, one-track singles with a joined artist,
missing artist or track foreign keys, duplicate `(track_id, single_id, artist_id)`
tuples, distinct URL candidates, and verified matches per entity type.
Save the HTML source date and exact source URL for every verified result.
