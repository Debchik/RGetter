# Transport

All HTTP goes through `pyrateyourmusic.transport`, which wraps
`unblock_requests.CloudflareSession` in FlareSolverr mode.

## FlareSolverr is required

rateyourmusic.com serves an interactive Cloudflare challenge that rejects plain
`requests` and TLS-fingerprint impersonation (`curl_cffi`) alike. Only a
FlareSolverr proxy — which drives a real headless browser — gets clearance.

The endpoint is resolved from the environment by `unblock_requests` using the
`PYRATEYOURMUSIC` prefix:

| Variable | Meaning |
| --- | --- |
| `PYRATEYOURMUSIC_FLARESOLVERR_URL` | FlareSolverr base URL (e.g. `http://localhost:8191`) |
| `PYRATEYOURMUSIC_FLARESOLVERR_TIMEOUT` | per-solve budget in ms (default 120000 here) |

`flaresolverr_url()` returns the configured endpoint (or `None`), which the live
test suite uses to skip when unset.

## Throttling

A minimum delay is enforced between requests (default 2.0 s):

```python
from pyrateyourmusic import set_delay
set_delay(3.0)
```

FlareSolverr solves are slow; the per-request timeout defaults to 130 s and the
solve budget to 120 s. Adjust the solve budget with `set_solve_timeout(ms)`.

## Coverage status

| Surface | Status |
| --- | --- |
| Chart listings (`/charts/…`) | **Fully reachable** — all metadata inline |
| Artist pages (`/artist/<slug>`) | **Fully reachable** — profile + discography |
| Release detail (`/release/<type>/…`) | **Protection-bound** — see fallback chain below |

Chart and artist pages carry the same metadata fields (title, artist, date, rating,
rating count, primary/secondary genres, descriptors) as release detail pages, so
bulk dataset construction does not require detail-page fetches at all.

## Release detail fallback chain

Release detail pages are rate-limited at the RYM origin independently of
Cloudflare. From datacenter IPs they return an HTML `503` page even after
Cloudflare clearance. `get_release` applies a three-step chain:

1. **Live fetch** via FlareSolverr — succeeds from residential IPs; 503s from
   datacenter/cloud IPs.
2. **Wayback Machine** (`unblock_requests.wayback_html`) — tried automatically on
   503. Snapshots are stale (often months old) but reliably carry title, artist,
   tracklist, rating, n_ratings, and cover art. Genres and descriptors may be
   absent in older snapshots.
3. **RuntimeError** — raised with guidance when both paths fail.

```python
from pyrateyourmusic import get_release

# succeeds live from residential IP, falls back to Wayback from datacenter IP,
# raises RuntimeError only when both fail
try:
    r = get_release("radiohead/ok-computer")
    # r.tracklist, r.rating, r.cover_url ... all populated from whichever source
    # worked; r.primary_genres may be empty if served from an old Wayback snapshot
    print(r, "wayback?" if not r.primary_genres else "live")
except RuntimeError as e:
    print("unavailable:", e)
    # fall back to chart / artist data, which always works
```

For bulk use, prefer chart or artist pages instead — they carry all the same
fields without triggering the origin block.

## Session lifecycle

The session is built lazily and cached. `reset_session()` discards it (e.g. to
pick up a changed environment); `set_solve_timeout()` also resets it.
