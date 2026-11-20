# pyrateyourmusic

`pyrateyourmusic` is a Python HTML scraper for
[rateyourmusic.com](https://rateyourmusic.com) (RYM / Sonemic). It parses
releases, artists, and charts into typed dataclasses. RYM is a
community-maintained music database with crowd ratings, a genre taxonomy,
mood and style descriptors, and full discographies. The client returns
`Release`, `ReleaseStub`, and `Artist` objects, and converts them to flat
`rym_*`-keyed dicts for cross-linking with other sources.

## Important caveats

RYM blocks bots. Live scraping needs a running
[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) instance.
Plain HTTP, `curl_cffi`, and TLS impersonation are all rejected. Even with
FlareSolverr, release detail pages often return a 503 from datacenter IPs.
HTML selectors are best-effort. They may need updates when RYM changes its
markup.

Set the solver endpoint before use:

```bash
export PYRATEYOURMUSIC_FLARESOLVERR_URL=http://localhost:8191
```

## Install

```bash
pip install -e .
```

## Use

```python
import pyrateyourmusic as p
p.set_delay(3.0)

# Charts, the reliable bulk source (title, artist, year, rating, genres inline)
for stub in p.top_albums("all-time")[:5]:
    print(stub, stub.rating, stub.genres)

# Artist + discography
artist = p.get_artist("radiohead")
print(artist.genres, artist.release_count)

# Release detail (tracklist and descriptors), may 503 from datacenter IPs
release = p.get_release("radiohead/ok-computer")
print(release.tracklist, release.descriptors)
```

## Canonical IDs

The `rym_id` anchor is the URL slug: `<artist>/<title>` for releases
(`radiohead/ok-computer`), `<slug>` for artists (`radiohead`).
`release_to_extra` and `artist_to_extra` emit flat `rym_*`-namespaced dicts.

## Reachability

Chart and artist pages are reliably reachable and carry the core metadata.
Release **detail** pages are also rate-limited at the origin and often
return a 503 from datacenter IPs. `get_release` raises `RuntimeError` in
that case. See [docs/transport.md](docs/transport.md).

## Spotify track-first matching (offline first)

For the current Spotify catalog, join **tracks.artist_rowids → artists.rowid**
using [sql/track_artists.yql](sql/track_artists.yql). There is **no need**
to join Spotify album tables. The resulting CSV has track + artist names and
IDs. Each input row generates possible RYM **song and single URLs** without
assuming the Spotify recording belongs to a single.

```bash
python -m pyrateyourmusic.matching ingest-tracks \
  examples/tracks_artists.example.csv matches.sqlite --kinds both
python -m pyrateyourmusic.matching export matches.sqlite candidates.csv
python -m pyrateyourmusic.matching export-links matches.sqlite spotify_candidates.csv
```

For existing saved RYM HTML, `verify-batch` reads a `url,html_path` manifest
and `export-verified` saves confirmed page matches and available release-level
genres/descriptors. **Guessed URLs are not matched tracks**.

- [Track-first workflow and commands](docs/track-first.md)
- [Instructions for local data/coding agent](LOCAL_AGENT_TASK.md)
- [Legacy one-track Spotify single workflow](docs/singles-matching.md)

Generating candidates does not send network requests. Fetching RYM HTML
requires an authorized data source; the package does not grant permission
to bypass access restrictions.

## Docs and examples

- Docs: [`docs/`](docs/), covering quickstart, transport, models, charts, ids, and dataset.
- Runnable examples: [`examples/`](examples/).
- Dataset export: [docs/dataset.md](docs/dataset.md).
- Source and licensing: [PROVENANCE.md](PROVENANCE.md).

## Related projects

Other TigreGotico clients for music metadata sources:

- [TigreGotico/pymusicbrainz](https://github.com/TigreGotico/pymusicbrainz), a MusicBrainz client.
- [TigreGotico/pydiscogs](https://github.com/TigreGotico/pydiscogs), a Discogs client.

## Tests

```bash
pip install -e '.[test]'
pytest -m "not live"   # offline fixture tests
pytest -m live         # live smoke (needs PYRATEYOURMUSIC_FLARESOLVERR_URL)
```

## License

Apache-2.0. See [LICENSE](LICENSE).
