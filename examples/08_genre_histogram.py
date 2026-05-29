"""Build a primary-genre histogram from a chart (no detail fetches needed).

    python examples/08_genre_histogram.py
"""
from collections import Counter

from pyrateyourmusic import set_delay, top_albums

set_delay(3.0)

counts: Counter = Counter()
for stub in top_albums("all-time"):
    counts.update(stub.primary_genres)

for genre, n in counts.most_common(15):
    print(f"  {n:>3}  {genre}")
