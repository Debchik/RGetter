"""Fetch a year/decade/genre chart by path or period.

    python examples/02_chart_by_year.py
"""
from pyrateyourmusic import get_chart, set_delay, top_albums

set_delay(3.0)

print("== Top albums of 2023 ==")
for stub in top_albums("2023")[:5]:
    print(f"  {stub} — {stub.rating}")

print("\n== Arbitrary chart path ==")
for stub in get_chart("/charts/top/album/1990s/")[:5]:
    print(f"  {stub} — {stub.rating}")
