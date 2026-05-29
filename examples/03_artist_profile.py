"""Fetch an artist profile and print the fact table.

    python examples/03_artist_profile.py radiohead
"""
import sys

from pyrateyourmusic import get_artist, set_delay

slug = sys.argv[1] if len(sys.argv) > 1 else "radiohead"
set_delay(3.0)

a = get_artist(slug)
print(a.name)
print(f"  formed:  {a.formed}")
print(f"  genres:  {', '.join(a.genres)}")
print(f"  members: {', '.join(a.members)}")
print(f"  aliases: {', '.join(a.aliases)}")
print(f"  related: {', '.join(a.related[:5])}")
print(f"  releases: {a.release_count}")
