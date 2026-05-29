"""Convert a release / artist into ``ExternalIds.extra`` dicts for metadatarr.

    python examples/06_external_ids.py
"""
import json

from pyrateyourmusic import (
    artist_to_extra,
    get_artist,
    release_to_extra,
    set_delay,
    top_albums,
)

set_delay(3.0)

stub = top_albums("all-time")[0]
print("release extra:")
print(json.dumps(release_to_extra(stub), indent=2, ensure_ascii=False))

artist = get_artist(stub.artist_id)
print("\nartist extra:")
print(json.dumps(artist_to_extra(artist), indent=2, ensure_ascii=False))
