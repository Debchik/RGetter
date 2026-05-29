"""Fetch a release detail page (tracklist + genres + descriptors).

Note: release detail pages are RYM's most heavily rate-limited surface and
frequently 503 from datacenter IPs — a residential exit may be required.

    python examples/05_release_detail.py radiohead/ok-computer
"""
import sys

from pyrateyourmusic import get_release, set_delay

rym_id = sys.argv[1] if len(sys.argv) > 1 else "radiohead/ok-computer"
set_delay(4.0)

try:
    r = get_release(rym_id)
except RuntimeError as exc:
    print(f"detail page unavailable: {exc}")
    sys.exit(1)

print(r)
print(f"  rating: {r.rating} ({r.n_ratings} ratings)")
print(f"  genres: {', '.join(r.genres)}")
print(f"  descriptors: {', '.join(r.descriptors)}")
print("  tracklist:")
for t in r.tracklist:
    print(f"    {t}  {t.duration}")
