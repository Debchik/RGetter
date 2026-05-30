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

## The 503 origin block

Release **detail** pages are rate-limited at the origin independently of
Cloudflare. From datacenter IPs they commonly return an HTML `503` page even
after clearance. `get_html` detects this body and raises a `RuntimeError` with
guidance rather than returning a junk page, so callers can catch it:

```python
from pyrateyourmusic import get_release
try:
    r = get_release("radiohead/ok-computer")
except RuntimeError:
    ...  # fall back to chart / artist data
```

Chart (`/charts/...`) and artist (`/artist/<slug>`) pages are not subject to this
block and carry the same metadata fields.

## Session lifecycle

The session is built lazily and cached. `reset_session()` discards it (e.g. to
pick up a changed environment); `set_solve_timeout()` also resets it.
