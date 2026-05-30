---
name: pyrateyourmusic
description: Query RateYourMusic charts, artists and album ratings for accessible voice-first access on behalf of users who cannot navigate the website.
---
# pyrateyourmusic — RateYourMusic for agents

## When to use

Use this skill when a user asks for music recommendations, chart rankings, artist discographies, or album ratings from RateYourMusic (RYM / Sonemic). This is the primary access path for blind and vision-impaired users who cannot navigate a Cloudflare-protected website visually. It is also appropriate for any voice-only interface where opening a browser is not an option.

## Install

```bash
pip install pyrateyourmusic   # plus a FlareSolverr solver for live access (heavy Cloudflare)
```

Set the solver endpoint before use:

```bash
export PYRATEYOURMUSIC_FLARESOLVERR_URL=http://localhost:8191
```

## Core operations

### `get_artist(slug: str) -> Artist`

Fetch an artist profile page by RYM slug.

- **Purpose:** retrieve biography metadata, genre tags, and a full discography listing.
- **Example:**
  ```python
  from pyrateyourmusic import get_artist
  artist = get_artist("radiohead")
  print(artist.name, artist.formed, artist.genres)
  ```
- **Returned fields:** `rym_id`, `name`, `url`, `formed`, `located`, `members`, `aliases`, `genres`, `related`, `notes`, `discography` (list of `ReleaseStub`), `release_count`.

---

### `get_discography(slug: str) -> List[ReleaseStub]`

Return only the release cards for an artist without the biography metadata.

- **Purpose:** enumerate an artist's catalogue when you only need titles, years and ratings.
- **Example:**
  ```python
  from pyrateyourmusic import get_discography
  for stub in get_discography("radiohead"):
      print(stub.position, stub.title, stub.year, stub.rating)
  ```
- **Returned fields:** same as `ReleaseStub` — see `get_chart` below.

---

### `get_chart(path: str = "/charts/top/album/all-time/") -> List[ReleaseStub]`

Fetch a single RYM chart page by its URL path.

- **Purpose:** retrieve ranked lists — top albums of all time, by year, by genre, etc.
- **Example:**
  ```python
  from pyrateyourmusic import get_chart
  entries = get_chart("/charts/top/album/2023/")
  for e in entries[:5]:
      print(e.position, e.artist, e.title, e.rating)
  ```
- **Returned fields:** `rym_id`, `title`, `artist`, `artist_id`, `url`, `release_type`, `year`, `date`, `rating`, `n_ratings`, `n_reviews`, `primary_genres`, `secondary_genres`, `descriptors`, `cover_url`, `position` (chart rank).

---

### `top_albums(period: str = "all-time") -> List[ReleaseStub]`

Convenience wrapper for `/charts/top/album/<period>/`.

- **Purpose:** the fastest path to "what are the top albums of X".
- **Example:**
  ```python
  from pyrateyourmusic import top_albums
  for stub in top_albums("1990s")[:10]:
      print(f"#{stub.position} {stub.artist} — {stub.title} ({stub.rating})")
  ```
- **Valid period values:** `"all-time"`, a year (`"2023"`), a decade (`"1990s"`).

---

### `get_release(rym_id: str, release_type: str = "album") -> Release`

Fetch a full release detail page including tracklist.

- **Purpose:** deep detail on a specific album — full tracklist, all genres, descriptors, ratings.
- **Example:**
  ```python
  from pyrateyourmusic import get_release
  release = get_release("radiohead/ok-computer")
  print(release.title, release.rating, release.primary_genres)
  for track in release.tracklist:
      print(track.position, track.title, track.duration)
  ```
- **Returned fields:** all `ReleaseStub` fields plus `tracklist` (list of `Track` with `position`, `title`, `duration`), `track_count`.
- **Warning:** release detail pages are heavily rate-limited and may be blocked from datacenter IPs. The library automatically falls back to an Internet Archive (Wayback Machine) snapshot. When served from Wayback, genres and descriptors may be absent. Prefer chart and artist pages for bulk metadata.

## Access notes

RYM is behind a heavy interactive Cloudflare deployment. A running FlareSolverr instance at `http://localhost:8191` (or the value of `PYRATEYOURMUSIC_FLARESOLVERR_URL`) is required for all live requests. Chart pages (`/charts/...`) and artist pages (`/artist/...`) are the reliable surfaces — they carry the same metadata fields as detail pages and are not additionally rate-limited. Individual release detail pages (`/release/...`) may return a 503 origin block from datacenter IPs; in that case the library automatically retries via Wayback Machine, but the snapshot may be stale and some fields (genres, descriptors) may be missing. When both paths fail a `RuntimeError` is raised with guidance to retry from a residential IP.

## Speaking the results (accessibility)

- **Chart entry:** read as rank, artist, album, year, rating — e.g. "Number 1: Radiohead — OK Computer, 1997, rated 4.21 out of 5."
- **Discography summary:** "Radiohead has 9 releases. Their highest rated is OK Computer from 1997 at 4.21. Genres: alternative rock, art rock."
- **Top albums of a year:** "Top albums of 2023: number 1, Mitski — The Land Is Inhospitable and So Are We, rated 3.98; number 2, ..."
- **Archive fallback:** if a release was served from an Internet Archive snapshot, say "Note: this detail is from a saved copy and may not reflect the current rating or full genre tags."
