# Dataset

pyrateyourmusic yields a music release/artist dataset suitable for
entity-resolution, genre-taxonomy and rating-distribution work — built entirely
from reachable chart and artist pages.

## Pipeline

1. **Crawl** charts and/or artists to JSONL (`export_chart`, `export_artists`),
   resumable and rate-limited.
2. **Read back** with `read_dataset`; summarise with `dataset_stats`.
3. **Publish** to the Hub by loading the JSONL into a `datasets.Dataset` and
   calling `push_to_hub` (the `dataset` optional extra installs `datasets`).

```python
from pyrateyourmusic.dataset import export_chart, export_artists, read_dataset

export_chart("/charts/top/album/all-time/", out_dir="rym_dataset", delay=3.0)
export_artists(["radiohead", "portishead"], out_dir="rym_dataset", delay=3.0)

rows = read_dataset("rym_dataset/releases.jsonl")
```

```python
from datasets import Dataset
ds = Dataset.from_list(read_dataset("rym_dataset/releases.jsonl"))
# ds.push_to_hub("you/rateyourmusic", config_name="releases", private=True)
```

## Configs

| Config | Grain | Columns (selected) |
| --- | --- | --- |
| `releases` | one row per release | `rym_id`, `title`, `artist`, `artist_id`, `year`, `rating`, `n_ratings`, `n_reviews`, `primary_genres`, `secondary_genres`, `descriptors`, `release_type` |
| `artists` | one row per artist | `rym_id`, `name`, `formed`, `located`, `genres`, `members`, `aliases`, `related`, `discography` |

Both join on the artist slug: `releases.artist_id` = `artists.rym_id`.
`export_artists(..., with_discography_releases=True)` (the default) also folds
each artist's discography into `releases.jsonl`, deduplicated by `rym_id`.

## Resumability

Each export keeps a `.done` sidecar (`releases.done`, `artists.done`) listing the
`rym_id`s / slugs already written. Re-running skips them, so an interrupted crawl
continues where it stopped. JSONL and the sidecar are flushed after every row.

## `export_jsonl`

For ad-hoc dumps, `export_jsonl(records, path)` writes any iterable of model
objects (or dicts) to a JSONL file, serialising each via its `as_dict`.

## Provenance

See [PROVENANCE.md](../PROVENANCE.md) for source, licensing and polite-scraping
terms.
