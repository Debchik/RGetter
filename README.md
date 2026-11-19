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

## Spotify single-track matching (offline first)

For a large Spotify catalog, the `pyrateyourmusic.matching` module creates
**unverified** RYM single and song URL candidates from a joined Spotify CSV,
deduplicates them in SQLite and supports explicit validation against saved
RYM HTML. The input is limited to `album_type=single` and `total_tracks=1`.

```bash
python -m pyrateyourmusic.matching ingest joined_singles.csv matches.sqlite
python -m pyrateyourmusic.matching export matches.sqlite candidate_urls.csv
```

See [docs/singles-matching.md](docs/singles-matching.md) for the required
Spotify column names, relation keys, SQL join, and verification limitations.
Candidate generation makes no network requests. Live RYM access requires
appropriate permissions under the site's terms of service.

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
