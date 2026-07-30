# Models

All models are dataclasses with an `as_dict` property for serialization.

## `Release`

Full release as parsed from a detail page.

| Field | Type | Notes |
| --- | --- | --- |
| `rym_id` | str | canonical `<artist>/<title>` slug, the anchor |
| `title` | str | |
| `artist` | str | full credited string (may be `"A & B"`) |
| `artist_id` | str | primary artist slug |

| Field | Type | Notes |
| --- | --- | --- |
| `url` | str | canonical release URL |
| `release_type` | str | `album` / `ep` / `single` / `comp` / ... |
| `year` | int? | parsed from `date` |
| `date` | str | raw release date |

| Field | Type | Notes |
| --- | --- | --- |
| `rating` | float? | average 0-5 |
| `n_ratings` | int? | |
| `n_reviews` | int? | |
| `primary_genres` | list[str] | |

| Field | Type | Notes |
| --- | --- | --- |
| `secondary_genres` | list[str] | |
| `descriptors` | list[str] | mood/style tags (detail pages only) |
| `tracklist` | list[`Track`] | |
| `cover_url` | str | |

Properties: `genres` (primary+secondary, deduped), `track_count`.

## `ReleaseStub`

A lightweight card from a chart or discography. Same scalar fields as `Release`
minus `tracklist`, plus `position` (chart rank). Carries genres/descriptors when
the source page renders them (charts do, discography rows do not). Call
`.get()` to fetch the full `Release` (subject to the 503 caveat).

## `Artist`

| Field | Type | Notes |
| --- | --- | --- |
| `rym_id` | str | artist slug, the anchor |
| `name` | str | |
| `url` | str | |
| `formed` | str | year + place |

| Field | Type | Notes |
| --- | --- | --- |
| `located` | str | |
| `members` | list[str] | bare names (instrument roles stripped) |
| `aliases` | list[str] | includes unlinked "Also Known As" values |
| `genres` | list[str] | |

| Field | Type | Notes |
| --- | --- | --- |
| `related` | list[str] | related artists |
| `notes` | str | |
| `discography` | list[`ReleaseStub`] | per-release year + rating |

Property: `release_count`.

## `Track`

`position` (`"1"`, `"A1"`), `title`, `duration` (raw `"4:13"`).

---
[← Transport](transport.md) · [Home](README.md) · [Charts →](charts.md)
