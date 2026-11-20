# Track-first Spotify → RYM matching (current recommended workflow)

**Use this route, not the one-track Spotify-singles ingest, for the current
20-million-track dataset.** No `albums`, `artist_albums`, Spotify single ID
or `total_tracks` is necessary. The old `matching ingest` command is
preserved for experiments with explicitly known Spotify single memberships.

## 1. Sources and exact joins

The November 2026 user-provided YSON sample of the intersected track table has
200 rows / 37 top-level fields. Its relevant columns:

- `sp_id`: Spotify track ID
- `sp_title`: Spotify track name
- `sp_rowid`: internal Spotify track row ID
- `artist_rowids`: list of internal Spotify artist row IDs
- `artist_cnt`: size of this list
- `isrc`, `duration_ms`, `original_release_date`: optional validation fields

The `artists` table contains `rowid`, `id`, `name`.

**Join:** each element of `tracks.artist_rowids` to `artists.rowid`.
Use `sql/track_artists.yql`, replace the two YTsaurus source paths, and
run it on the full tables (NOT independent `LIMIT 100` extracts).

In the provided 200-track sample, `artist_cnt` agreed with
`len(artist_rowids)` for all 200 and there were 291 track–artist links. These
numbers are sample-specific and cannot predict production coverage.

The query assumes `artist_rowids` has a YQL `List` type. If the schema says
`Yson`, first convert using a documented Yson conversion into a typed list
(e.g. `Yson::ConvertTo(..., List<Uint64>)` if the stored elements are Uint64),
then `FLATTEN LIST BY`. Check the **actual table schema**, not the exported
YSON textual representation. Ensure the type matches `artists.rowid`.

## 2. Exact input CSV

The YQL export must produce a UTF-8 CSV with this header (order arbitrary):

```text
spotify_track_id,spotify_track_name,spotify_artist_id,artist_name,isrc,duration_ms,original_release_date
```

The first four fields are required and non-empty. The last three are optional.
One input row means **one Spotify track × one credited artist**; keep all artists
on collaborations. There is no album ID and no inferred Spotify single
membership.

First export 10,000–50,000 *tracks* from a stable sampled source and join
against the COMPLETE artists table. Do not sample the artist table independently.
Count how many IDs were lost in the join, as well as multi-artist expansion.

Use a distributed YTsaurus output table and stream the CSV download; do not
collect 20 million source rows in the YQL UI or in local Python memory.

## 3. Local Python commands

On branch `feat/singles-matching-pipeline`:

```bash
python -m pip install -e '.[test]'
python -m pytest tests/test_matching_tracks.py tests/test_matching.py -q

mkdir -p data
python -m pyrateyourmusic.matching ingest-tracks \
  tracks_artists.csv data/rym_candidates.sqlite --limit 10000

# URL hypotheses (NOT verified matches):
python -m pyrateyourmusic.matching export \
  data/rym_candidates.sqlite data/url_candidates.csv

# All links back to source Spotify IDs, including candidate kind/provenance:
python -m pyrateyourmusic.matching export-links \
  data/rym_candidates.sqlite data/spotify_rym_candidates.csv
```

Default `ingest-tracks` creates two kinds of candidate for each track-artist
pair: `/song/<artist>/<track>/` and
`/release/single/<artist>/<track>/`. Each kind may get several conservative
punctuation/underscore URL variants. You can specify `--kinds song` or
`--kinds single` for a focused experiment.

Run `ingest-tracks` again on the same CSV/DB to resume: source rows,
entity keys, candidate URLs and source associations are deduplicated by SQLite.
Note that `INSERT OR IGNORE` does not update changed source metadata:
use a new DB for a refreshed catalog snapshot.

**IMPORTANT:** `spotify_single_id` is intentionally blank for track-first
rows. It is **not** inferred from `sp_title`. The reported
`spotify_join_method = track_artist_id_join` refers solely to the verified
Spotify track-to-artist ID relationship. All RYM URLs are guesses until
verified against actual page content.

## 4. Verify pages and extract RYM metadata from provided HTML

Network retrieval is **separate**. Use legally authorized access or saved HTML
already available to you. Do not treat blocked requests as missing records.

For a single page:

```bash
python -m pyrateyourmusic.matching verify-html \
  data/rym_candidates.sqlite \
  https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/ \
  path/to/saved_yung_hefner.html
```

For many local pages create `html_manifest.csv`:

```csv
url,html_path
https://rateyourmusic.com/release/single/morgenshtern/yung-hefner/,html/yung_hefner.html
```

Then run:

```bash
python -m pyrateyourmusic.matching verify-batch \
  data/rym_candidates.sqlite html_manifest.csv

python -m pyrateyourmusic.matching export-verified \
  data/rym_candidates.sqlite data/verified_rym.csv
```

`verify-html` and `verify-batch` require the canonical `og:url`, and
artist and title from the page to match the candidate. Missing/blocked markup
does not become a verified match. For verified RYM single release pages the
export stores JSON metadata: RYM release-level genres, descriptors, rating,
date and actual `/song/` links from its tracklist. For RYM song pages it
currently stores identity only (the supplied example has no song-level
descriptors).

A verified RYM page identity is **not proof of audio identity** with the
Spotify recording. In particular, metadata from a RYM single belongs to that
release, and should not be silently converted to ground-truth labels for
the Spotify recording without a separate validation step.

## 5. Quality gates before attempting full-scale lookup

Record statistics at each stage:
1. Unique Spotify `sp_id` before and after artist JOIN; number of missing
   artist IDs; number of track–artist rows and duplicate associations.
2. Unique `artist_name + track_name` entity keys and unique URL candidates.
3. Fraction of saved RYM pages that verify, separately for `song` and `single`.
4. False positive rate estimated on a **manually labelled** stratified sample
   of 100–300 URLs, including shared titles, featured artists and releases
   with multiple versions.
5. Share of verified RYM single pages with genres and descriptors, as opposed
   to song pages which may not provide these fields.

Never claim RYM coverage before the URL hypotheses are actually checked.
Prioritize unique URLs; millions of rows can reference the same song/release.
Measure disk use and throughput on a small input before 20M-row scale.

## 6. Scope and restrictions

This code does **not** contain a bulk remote URL fetcher. The existing
`pyrateyourmusic.transport` fetches pages, but authorized access to RYM
is a separate prerequisite. RYM's published access restrictions matter;
do not assume that installing or running FlareSolverr grants permission.
Do not implement anti-bot bypasses or evade site rate limits.

See also `docs/singles-matching.md` for the older album-assisted strategy.
