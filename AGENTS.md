# AGENTS — pyrateyourmusic

## What this is

An HTML scraper for rateyourmusic.com that parses page markup into typed
dataclasses for releases, artists and charts, plus external-ID dict converters
and a resumable JSONL dataset exporter. CSS selectors are best-effort and may
break if RYM changes its markup.

## Layout

| Path | Role |
| --- | --- |
| `pyrateyourmusic/__init__.py` | public API surface (`__all__`) |
| `pyrateyourmusic/transport.py` | FlareSolverr session, throttling, 503 detection |
| `pyrateyourmusic/_clean.py` | text/number/slug normalisation helpers |
| `pyrateyourmusic/_parse.py` | BeautifulSoup parsers for chart / artist / release HTML |
| `pyrateyourmusic/models.py` | `Release`, `ReleaseStub`, `Artist`, `Track` dataclasses |
| `pyrateyourmusic/release.py` | `get_release` (detail pages) |
| `pyrateyourmusic/artist.py` | `get_artist`, `get_discography` |
| `pyrateyourmusic/charts.py` | `get_chart`, `top_albums` |
| `pyrateyourmusic/ids.py` | `release_to_extra`, `artist_to_extra` |
| `pyrateyourmusic/dataset.py` | resumable export + `export_jsonl` |
| `tests/` | offline fixture tests + `test_live.py` (`-m live`) |

## Conventions

- All HTTP goes through `transport.get_html`; never hit the network elsewhere.
- FlareSolverr is **required**; the endpoint is read from
  `PYRATEYOURMUSIC_FLARESOLVERR_URL` by `unblock_requests` (prefix
  `PYRATEYOURMUSIC`).
- The `rym_id` anchor is the URL slug — `<artist>/<title>` for releases,
  `<slug>` for artists. Keep it canonical.
- Parsers are tolerant: every field is optional; missing markup yields a default,
  never an exception.
- New parsing? Add a trimmed offline fixture under `tests/fixtures/` and assert
  against `_parse`. Keep `test_live.py` to 1-2 page fetches.

## Reachability reality

Chart and artist pages are reachable via FlareSolverr. Release **detail** pages
are rate-limited at the origin and routinely 503 from datacenter IPs;
`get_html` raises `RuntimeError` on that body so callers can fall back to chart /
artist data. The live smoke tests therefore exercise charts + artists only.

## Running

```bash
pip install -e '.[test]'
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -m "not live"   # offline
PYRATEYOURMUSIC_FLARESOLVERR_URL=http://host:8191 pytest -m live
```
