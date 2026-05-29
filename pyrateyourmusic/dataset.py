"""Resumable JSONL dataset export for rateyourmusic.com.

Two Hugging Face-publishable configs:

- ``releases`` — one row per release (from charts or discographies), with
  title, artist, year, rating, rating/review counts, genres and descriptors.
- ``artists``  — one row per artist, with the fact table and discography.

Exports are resumable: ids already recorded in a ``.done`` sidecar are skipped,
so an interrupted run continues where it stopped. All network access is polite
(``set_delay``) and per-item failures are logged and skipped, not fatal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, List, Set

from pyrateyourmusic.artist import get_artist
from pyrateyourmusic.charts import get_chart
from pyrateyourmusic.transport import set_delay


def _load_done(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def export_chart(
    chart_path: str = "/charts/top/album/all-time/",
    out_dir: str = "rym_dataset",
    delay: float = 2.0,
) -> Path:
    """Fetch a chart page and append its releases to ``releases.jsonl``.

    Resumable via a ``releases.done`` sidecar keyed on ``rym_id``.

    Returns:
        Path to the written ``releases.jsonl`` file.
    """
    set_delay(delay)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    jsonl = out / "releases.jsonl"
    done_path = out / "releases.done"
    done = _load_done(done_path)

    stubs = get_chart(chart_path)
    with open(jsonl, "a", encoding="utf-8") as fh, open(done_path, "a", encoding="utf-8") as df:
        for n, stub in enumerate(stubs, 1):
            if stub.rym_id in done:
                continue
            fh.write(json.dumps(stub.as_dict, ensure_ascii=False) + "\n")
            fh.flush()
            df.write(stub.rym_id + "\n")
            df.flush()
            done.add(stub.rym_id)
            sys.stderr.write(f"\r  releases {n}/{len(stubs)} ({stub.rym_id})   ")
            sys.stderr.flush()
    sys.stderr.write("\n")
    return jsonl


def export_artists(
    slugs: Iterable[str],
    out_dir: str = "rym_dataset",
    delay: float = 2.0,
    with_discography_releases: bool = True,
) -> Path:
    """Fetch each artist slug, append to ``artists.jsonl`` and, optionally,
    append every discography entry to ``releases.jsonl``.

    Resumable via an ``artists.done`` sidecar keyed on the artist slug.

    Returns:
        Path to the written ``artists.jsonl`` file.
    """
    set_delay(delay)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    a_jsonl = out / "artists.jsonl"
    a_done_path = out / "artists.done"
    a_done = _load_done(a_done_path)

    r_jsonl = out / "releases.jsonl"
    r_done_path = out / "releases.done"
    r_done = _load_done(r_done_path)

    slugs = [str(s).strip("/").split("/")[-1] for s in slugs]
    total = len(slugs)
    with open(a_jsonl, "a", encoding="utf-8") as af, \
            open(a_done_path, "a", encoding="utf-8") as adf, \
            open(r_jsonl, "a", encoding="utf-8") as rf, \
            open(r_done_path, "a", encoding="utf-8") as rdf:
        for n, slug in enumerate(slugs, 1):
            if slug in a_done:
                continue
            try:
                artist = get_artist(slug)
            except Exception as exc:  # noqa: BLE001 - skip & continue
                sys.stderr.write(f"\n  skip {slug}: {exc}\n")
                continue
            af.write(json.dumps(artist.as_dict, ensure_ascii=False) + "\n")
            af.flush()
            adf.write(slug + "\n")
            adf.flush()
            a_done.add(slug)
            if with_discography_releases:
                for stub in artist.discography:
                    if stub.rym_id in r_done:
                        continue
                    rf.write(json.dumps(stub.as_dict, ensure_ascii=False) + "\n")
                    rf.flush()
                    rdf.write(stub.rym_id + "\n")
                    rdf.flush()
                    r_done.add(stub.rym_id)
            sys.stderr.write(f"\r  artists {n}/{total} ({slug})   ")
            sys.stderr.flush()
    sys.stderr.write("\n")
    return a_jsonl


def export_jsonl(records: Iterable, path: str) -> Path:
    """Write an iterable of model objects (or dicts) to a JSONL file.

    Each item is serialised via its ``as_dict`` property when present.

    Returns:
        Path to the written file.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        for rec in records:
            row = rec.as_dict if hasattr(rec, "as_dict") else rec
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out


def read_dataset(path: str) -> List[dict]:
    """Load an exported JSONL file back into a list of dicts."""
    rows: List[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def dataset_stats(path: str) -> dict:
    """Summarise an exported releases/artists JSONL file."""
    rows = read_dataset(path)
    with_rating = sum(1 for r in rows if r.get("rating") is not None)
    with_genres = sum(1 for r in rows if r.get("primary_genres") or r.get("genres"))
    return {
        "rows": len(rows),
        "with_rating": with_rating,
        "with_genres": with_genres,
    }
