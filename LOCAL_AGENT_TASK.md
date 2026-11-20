# Task for the local coding/data agent: Spotify → RYM (track-first)

## Goal
Build a reproducible, audited pipeline from our **target intersected Spotify
track population (~20 million tracks)** to **candidate RYM song and single
pages**, then verify only the RYM HTML pages available through authorized
access. Maximize useful matches. No Spotify `albums` or `artist_albums`
joins are required for this iteration.

**Repo:** https://github.com/Debchik/RGetter
**Working branch:** `feat/singles-matching-pipeline`
**Read first:** `docs/track-first.md`, `sql/track_artists.yql`.
Never merge or push to `dev` without permission.

## Phase A — Get the right rows from YTsaurus

1. Locate the **FULL** source table for target Spotify tracks (the uploaded
   200-row YSON sample is not the full dataset). Inspect its table schema.
   Relevant columns: `sp_id, sp_rowid, sp_title, artist_rowids, artist_cnt,
   isrc, duration_ms, original_release_date`.
2. Locate the **FULL** Spotify `artists` table. Inspect
   `rowid, id, name` and verify `rowid` type.
3. Adjust paths in `sql/track_artists.yql`. Unnest
   `tracks.artist_rowids` via YQL `FLATTEN LIST BY`, then **INNER JOIN
   artists.rowid**. If `artist_rowids` is Yson-typed, convert to an
   appropriately typed list before flattening; check actual type first.
4. Use a **stable 10k–50k source-track pilot**, selected before unnesting;
   keep the full artists table for the join. Produce one row per track–artist.
5. Count and report:
   - original distinct Spotify IDs in pilot;
   - distinct IDs surviving the join;
   - missing artist references;
   - output rows and unique `(spotify_track_id, spotify_artist_id)` pairs;
   - fraction with empty track/artist names.
   Alert rather than silently discard missing IDs.
6. Persist the pilot as a YTsaurus output table, then **stream** it into UTF-8
   CSV; do not use YQL UI result download for 20M rows. The header must be:
   `spotify_track_id,spotify_track_name,spotify_artist_id,artist_name,
   isrc,duration_ms,original_release_date`. First four columns mandatory.
   Quote CSV correctly, including artist/title commas and quotes.

## Phase B — Generate URL guesses locally

```bash
git fetch origin
git checkout feat/singles-matching-pipeline
python -m pip install -e '.[test]'
python -m pytest tests/test_matching_tracks.py tests/test_matching.py -q

mkdir -p data
python -m pyrateyourmusic.matching ingest-tracks \
  tracks_artists.csv data/rym_candidates.sqlite --limit 10000 --kinds both

python -m pyrateyourmusic.matching export \
  data/rym_candidates.sqlite data/candidate_urls.csv
python -m pyrateyourmusic.matching export-links \
  data/rym_candidates.sqlite data/spotify_to_rym_candidates.csv
```

Check `--help` before running. Start with the pilot, not all 20M.
`--kinds song` and `--kinds single` are optional experiments.
A guessed `/release/single/{artist}/{track}/` is not proof that the Spotify
track belongs to a Spotify single. The release ID is intentionally blank.
Keep all collaborations; deduplicate candidate URLs by URL before further work.
Re-running the ingest with unchanged data/SQLite path must not add duplicates.

## Phase C — Validate real RYM pages, when access is permitted

RYM automated access may require site authorization. Do not use anti-bot
bypasses, mass unsolicited fetching or evasive proxy rotation. If approved
live retrieval is unavailable, stop at URL export and test with pre-saved HTML.

Make a UTF-8 CSV manifest `url,html_path` of actually obtained HTML files
(see `docs/track-first.md`). The URL MUST be the candidate's intended URL.

```bash
python -m pyrateyourmusic.matching verify-batch \
  data/rym_candidates.sqlite html_manifest.csv

python -m pyrateyourmusic.matching export-verified \
  data/rym_candidates.sqlite data/verified_rym.csv
```

The verifier checks page canonical URL and artist/title; a 200, challenge
page or stale unrelated HTML is **not** a confirmed match.
`verified_rym.csv` includes Spotify IDs, page kind, verified RYM URL and
`metadata_json`. RYM single page metadata has genres/descriptors/rating
when present; saved RYM song pages may have only identity.
**Release-level tags must not silently become track-level ground truth.**

## Phase D — What you must report

- SQL/YQL query version, actual YT source and output paths, table schema types.
- Counts before/after join, unmatched artist IDs, duplicate associations.
- Candidate URLs by kind (unique), SQLite DB file size and processing rate.
- Number of saved HTML pages tested, how many verified, and reasons for failure.
- Number of verified pages with non-empty genres/descriptors.
- Small manually checked positive and negative examples; record ambiguity.
- Exact commands executed, tests run and any failures.
- A final `verified_rym.csv` sample with provenance (never claim candidate
  URLs are confirmed). Do **not** commit the 20M rows, secrets or downloaded
  personal data to GitHub.

**Stop criteria:** if source YTsaurus schema prevents the JOIN, report the
exact offending field and type. If RYM access isn't authorized, do not fetch
live pages; produce and validate the offline candidates only.
