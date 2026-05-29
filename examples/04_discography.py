"""Print an artist's discography sorted by rating.

    python examples/04_discography.py radiohead
"""
import sys

from pyrateyourmusic import get_discography, set_delay

slug = sys.argv[1] if len(sys.argv) > 1 else "radiohead"
set_delay(3.0)

disco = get_discography(slug)
rated = [d for d in disco if d.rating is not None]
for d in sorted(rated, key=lambda r: r.rating or 0, reverse=True)[:15]:
    yr = d.year or "----"
    print(f"  {d.rating}  {yr}  {d.title}")
