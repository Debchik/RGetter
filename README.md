# pyrateyourmusic

Python HTML scraper for [rateyourmusic.com](https://rateyourmusic.com)
(RYM / Sonemic) — releases, artists and charts as typed dataclasses.

RYM is a community music database with crowd ratings, a deep genre taxonomy,
mood/style descriptors and full discographies. This client returns
`Release`, `ReleaseStub` and `Artist` objects and converts them to
flat `rym_*`-keyed dicts for cross-linking.

## Important caveats

**RYM aggressively blocks bots.** Live scraping requires a running
[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) instance — plain
HTTP, `curl_cffi`, and TLS impersonation are all rejected. Even with FlareSolverr,
release detail pages commonly 503 from datacenter IPs. HTML selectors are
best-effort and may need updating when RYM changes its markup.

Set the solver endpoint before use:

```bash
export PYRATEYOURMUSIC_FLARESOLVERR_URL=http://localhttp://localhost:8191
```

## Install

```bash
pip install -e .
```

## Use

```python
import pyrateyourmusic as p
p.set_delay(3.0)

# Charts — reliable bulk source (title, artist, year, rating, genres inline)
for stub in p.top_albums("all-time")[:5]:
    print(stub, stub.rating, stub.genres)

# Artist + discography
artist = p.get_artist("radiohead")
print(artist.genres, artist.release_count)

# Release detail (tracklist + descriptors) — may 503 from datacenter IPs
release = p.get_release("radiohead/ok-computer")
print(release.tracklist, release.descriptors)
```

## Canonical IDs

The `rym_id` anchor is the URL slug: `<artist>/<title>` for releases
(`radiohead/ok-computer`), `<slug>` for artists (`radiohead`).
`release_to_extra` / `artist_to_extra` emit flat `rym_*`-namespaced dicts.

## Reachability

Chart and artist pages are reliably reachable and carry the core metadata.
Release **detail** pages are additionally rate-limited at the origin and often
return a 503 from datacenter IPs; `get_release` raises `RuntimeError` in that
case. See [docs/transport.md](docs/transport.md).

## Docs & examples

- Docs: [`docs/`](docs/) — quickstart, transport, models, charts, ids, dataset.
- Runnable examples: [`examples/`](examples/).
- Dataset export: [`docs/dataset.md`](docs/dataset.md).
- Source & licensing: [`PROVENANCE.md`](PROVENANCE.md).

## Tests

```bash
pip install -e '.[test]'
pytest -m "not live"   # offline fixture tests
pytest -m live         # live smoke (needs PYRATEYOURMUSIC_FLARESOLVERR_URL)
```
