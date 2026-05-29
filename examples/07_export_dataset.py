"""Export a chart and a handful of artists to a resumable JSONL dataset.

    python examples/07_export_dataset.py
"""
from pyrateyourmusic.dataset import (
    dataset_stats,
    export_artists,
    export_chart,
)

OUT = "rym_dataset"

releases = export_chart("/charts/top/album/all-time/", out_dir=OUT, delay=3.0)
print("releases ->", releases)
print("  stats:", dataset_stats(str(releases)))

artists = export_artists(["radiohead", "portishead"], out_dir=OUT, delay=3.0)
print("artists ->", artists)
print("  stats:", dataset_stats(str(artists)))
