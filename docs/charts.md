# Charts

Chart pages are the reliable, rich bulk source. Each entry already carries
title, artist, date, average rating, rating and review counts, and primary
and secondary genres. No per-release detail fetch is needed.

```python
from pyrateyourmusic import get_chart, top_albums

top_albums("all-time")              # /charts/top/album/all-time/
top_albums("2023")                  # /charts/top/album/2023/
top_albums("1990s")                 # /charts/top/album/1990s/
get_chart("/charts/top/album/all-time/genre/jazz/")
```

`get_chart(path)` takes any chart path. `top_albums(period)` is a thin
wrapper for the common `/charts/top/album/<period>/` shape.

## Returned data

Each entry is a `ReleaseStub` with `position` set to its in-page rank:

```python
for stub in top_albums("all-time"):
    print(stub.position, stub.rym_id, stub.rating, stub.n_ratings,
          stub.primary_genres, stub.secondary_genres)
```

A single chart page yields about 40 entries. Walk multiple pages by passing
the paginated path (RYM uses `/N/` suffixes on chart URLs).

## Descriptors

Mood and style **descriptors** render on release *detail* pages, not on the
all-time or year charts. The `descriptors` field on chart stubs is populated
only when a chart variant exposes the descriptor line. For full descriptors,
use `get_release` (subject to the 503 caveat in [transport.md](transport.md)).

---
[← Models](models.md) · [Home](README.md) · [IDs →](ids.md)