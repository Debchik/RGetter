"""Fetch the all-time top albums chart and print the top 10.

    PYRATEYOURMUSIC_FLARESOLVERR_URL=http://localhost:8191 python examples/01_top_albums.py
"""
from pyrateyourmusic import set_delay, top_albums

set_delay(3.0)

for stub in top_albums("all-time")[:10]:
    pos = f"{stub.position:>2}" if stub.position else " ?"
    print(f"{pos}. {stub} — {stub.rating} ({stub.n_ratings:,} ratings)")
    print(f"      genres: {', '.join(stub.genres)}")
