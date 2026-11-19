# Provenance

## Source

Data is scraped from [rateyourmusic.com](https://rateyourmusic.com) (RYM /
Sonemic), a community-maintained music database of releases, artists, crowd
ratings, a genre taxonomy and mood/style descriptors.

`pyrateyourmusic` reads **structured metadata only** — titles, artist credits,
release dates, ratings, genres, descriptors and tracklists. It does not download,
host or redistribute any audio.

## Licensing

RYM content is contributed by its community. Use is governed by the site's terms
of service. Any dataset derived with this tool is for **research and
non-commercial** use; attribute RateYourMusic and link back to the source page
(each record carries a canonical `rym_id` and `url`).

## Polite scraping

- A minimum delay between requests (`set_delay`, default 5.0 s).
- FlareSolverr is used to satisfy Cloudflare; no additional headed browser.
- Crawls are seeded from charts and named artists, not blind link-following.
- Release detail pages are rate-limited at the origin and may 503; the client
  surfaces that rather than hammering — back off and slow down.

Respect `robots.txt` and the site's terms. This client is intended for
legitimate metadata and dataset work, not bulk mirroring.
