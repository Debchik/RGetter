# Quickstart

## Install

```bash
pip install -e .            # core: requests, beautifulsoup4, unblock_requests
pip install -e '.[dataset]' # adds `datasets` for Hugging Face export
```

## Configure FlareSolverr (required)

rateyourmusic.com is behind a heavy interactive Cloudflare deployment. A
[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) proxy is required to
obtain clearance — plain HTTP and TLS impersonation are rejected. Point the
client at one:

```bash
export PYRATEYOURMUSIC_FLARESOLVERR_URL=http://192.168.1.116:8191
```

The transport reads this variable when it builds the session. No other
configuration is needed.

## First calls

```python
import pyrateyourmusic as p

p.set_delay(3.0)  # polite: seconds between requests

# Charts — the reliable bulk source (title, artist, year, rating, genres inline)
for stub in p.top_albums("all-time")[:5]:
    print(stub, stub.rating, stub.genres)

# Artist profile + discography
artist = p.get_artist("radiohead")
print(artist.name, artist.genres, artist.release_count)

# Release detail (tracklist + descriptors) — see the caveat below
release = p.get_release("radiohead/ok-computer")
print(release.tracklist)
```

## A note on release detail pages

Release detail pages (`/release/<type>/<artist>/<title>/`) are RYM's most
heavily rate-limited surface and frequently answer a `503` origin block from
datacenter IPs — `get_release` raises `RuntimeError` in that case. Charts and
artist pages carry the same title / artist / year / rating / genre data and stay
reachable, so prefer them for bulk work and reserve detail fetches (which add
the tracklist and descriptors) for a residential exit. See
[transport.md](transport.md).
