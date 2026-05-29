# pyrateyourmusic

Python scraper / API client for [rateyourmusic.com](https://rateyourmusic.com)
(RYM / Sonemic) — releases, artists and charts as typed dataclasses.

RYM is a community music database with crowd ratings, a deep genre taxonomy,
mood/style descriptors and full discographies. This client returns
`Release`, `ReleaseStub` and `Artist` objects and converts them to
`ExternalIds.extra` dicts for cross-linking.

## FlareSolverr required

rateyourmusic.com sits behind a heavy interactive Cloudflare deployment; only a
[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) proxy gets through.
Point the client at one:

```bash
export PYRATEYOURMUSIC_FLARESOLVERR_URL=http://192.168.1.116:8191
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
`release_to_extra` / `artist_to_extra` emit `rym_*`-namespaced
`ExternalIds.extra` dicts.

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
