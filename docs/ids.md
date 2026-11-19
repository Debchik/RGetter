# IDs & External ID dicts

## The `rym_id` anchor

Every object carries an `rym_id` taken from the URL slug. For releases this short slug is **not unique across release types**; use `rym_release_key` (`release_type/rym_id`) as the collision-safe key:

- **Release**: `<artist>/<title>`, e.g. `radiohead/ok-computer`.
- **Artist**: `<slug>`, e.g. `radiohead`.

These are the cross-link anchors used for joining releases and artists across
datasets and integrations.

## Converters

`pyrateyourmusic.ids` flattens models into plain dicts. Keys are
namespaced with `rym_`. List values are JSON-encoded. Scalars are
stringified. Empty values are omitted.

```python
from pyrateyourmusic import release_to_extra, artist_to_extra
release_to_extra(stub)
# {
#   "rym_id": "radiohead/ok-computer",
#   "rym_url": "https://rateyourmusic.com/release/album/radiohead/ok-computer/",
#   "rym_title": "OK Computer",
#   "rym_artist": "Radiohead",
#   "rym_artist_id": "radiohead",
#   "rym_type": "album",
#   "rym_year": "1997",
#   "rym_rating": "4.23",
#   "rym_n_ratings": "136046",
#   "rym_primary_genres": "[\"Alternative Rock\", \"Art Rock\"]",
#   ...
# }
artist_to_extra(artist)
# { "rym_artist_id": "radiohead", "rym_artist_name": "Radiohead",
#   "rym_genres": "[...]", "rym_members": "[...]", ... }
```

`release_to_extra` accepts both `Release` and `ReleaseStub`. The full key
namespace is documented in the `pyrateyourmusic/ids.py` module docstring.

---
[← Charts](charts.md) · [Home](README.md) · [Dataset →](dataset.md)
