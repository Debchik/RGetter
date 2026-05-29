from pyrateyourmusic.charts import _stubs_from_html
from pyrateyourmusic.dataset import dataset_stats, export_jsonl, read_dataset


def test_export_and_read_roundtrip(tmp_path, chart_html):
    stubs = _stubs_from_html(chart_html)
    out = export_jsonl(stubs, str(tmp_path / "releases.jsonl"))
    rows = read_dataset(str(out))
    assert len(rows) == len(stubs)
    assert rows[0]["rym_id"] == stubs[0].rym_id
    assert rows[0]["rating"] == stubs[0].rating


def test_dataset_stats(tmp_path, chart_html):
    stubs = _stubs_from_html(chart_html)
    out = export_jsonl(stubs, str(tmp_path / "releases.jsonl"))
    stats = dataset_stats(str(out))
    assert stats["rows"] == len(stubs)
    assert stats["with_rating"] >= 1
    assert stats["with_genres"] >= 1
