import pyrateyourmusic.dataset as dataset_mod
from pyrateyourmusic.charts import _stubs_from_html
from pyrateyourmusic.dataset import (
    dataset_stats,
    export_artists,
    export_chart,
    export_jsonl,
    read_dataset,
)
from pyrateyourmusic.models import Artist, ReleaseStub


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


def test_export_chart_is_resumable(monkeypatch, tmp_path, chart_html):
    stubs = _stubs_from_html(chart_html)
    monkeypatch.setattr(dataset_mod, "get_chart", lambda path: stubs)
    monkeypatch.setattr(dataset_mod, "set_delay", lambda seconds: None)

    out_dir = tmp_path / "rym_dataset"
    export_chart(out_dir=str(out_dir))
    first_rows = read_dataset(str(out_dir / "releases.jsonl"))
    assert len(first_rows) == len(stubs)

    # A second run against the same output dir must not duplicate rows
    # already recorded in the .done sidecar.
    export_chart(out_dir=str(out_dir))
    second_rows = read_dataset(str(out_dir / "releases.jsonl"))
    assert len(second_rows) == len(stubs)


def test_export_artists_is_resumable(monkeypatch, tmp_path):
    artist = Artist(
        rym_id="radiohead",
        name="Radiohead",
        url="https://rateyourmusic.com/artist/radiohead",
        discography=[
            ReleaseStub(
                rym_id="radiohead/ok-computer",
                title="OK Computer",
                artist="Radiohead",
                url="https://rateyourmusic.com/release/album/radiohead/ok-computer/",
                artist_id="radiohead",
            )
        ],
    )
    monkeypatch.setattr(dataset_mod, "get_artist", lambda slug: artist)
    monkeypatch.setattr(dataset_mod, "set_delay", lambda seconds: None)

    out_dir = tmp_path / "rym_dataset"
    export_artists(["radiohead"], out_dir=str(out_dir))
    artists = read_dataset(str(out_dir / "artists.jsonl"))
    releases = read_dataset(str(out_dir / "releases.jsonl"))
    assert len(artists) == 1
    assert len(releases) == 1

    # Re-running with the same slug must skip the already-recorded artist
    # and its discography releases (resumable via the .done sidecars).
    export_artists(["radiohead"], out_dir=str(out_dir))
    assert len(read_dataset(str(out_dir / "artists.jsonl"))) == 1
    assert len(read_dataset(str(out_dir / "releases.jsonl"))) == 1


def test_export_artists_skips_failures(monkeypatch, tmp_path):
    def _get_artist(slug):
        if slug == "broken":
            raise RuntimeError("503 origin block (mocked)")
        return Artist(
            rym_id=slug,
            name=slug.title(),
            url=f"https://rateyourmusic.com/artist/{slug}",
        )

    monkeypatch.setattr(dataset_mod, "get_artist", _get_artist)
    monkeypatch.setattr(dataset_mod, "set_delay", lambda seconds: None)

    out_dir = tmp_path / "rym_dataset"
    export_artists(["radiohead", "broken", "portishead"], out_dir=str(out_dir))
    artists = read_dataset(str(out_dir / "artists.jsonl"))
    assert {a["rym_id"] for a in artists} == {"radiohead", "portishead"}


def test_export_artists_can_add_discography_after_metadata_only(monkeypatch, tmp_path):
    """An artists.done entry must not suppress a later discography export."""
    import pyrateyourmusic.dataset as dataset_mod
    from pyrateyourmusic.models import Artist, ReleaseStub

    def artist(_):
        return Artist(
            rym_id="radiohead", name="Radiohead", url="https://rateyourmusic.com/artist/radiohead",
            discography=[ReleaseStub(
                rym_id="radiohead/ok-computer", title="OK Computer", artist="Radiohead",
                release_type="album", url="https://rateyourmusic.com/release/album/radiohead/ok-computer/",
            )],
        )

    monkeypatch.setattr(dataset_mod, "get_artist", artist)
    monkeypatch.setattr(dataset_mod, "set_delay", lambda s: None)
    export_artists(["radiohead"], out_dir=str(tmp_path), with_discography_releases=False)
    export_artists(["radiohead"], out_dir=str(tmp_path), with_discography_releases=True)
    assert len(read_dataset(str(tmp_path / "artists.jsonl"))) == 1
    assert len(read_dataset(str(tmp_path / "releases.jsonl"))) == 1


def test_release_types_do_not_collide_in_done(monkeypatch, tmp_path):
    """album/A/title and single/A/title have distinct export keys."""
    album = ReleaseStub(
        rym_id="a/title", title="Title", artist="A",
        url="https://rateyourmusic.com/release/album/a/title/", release_type="album")
    single = ReleaseStub(
        rym_id="a/title", title="Title", artist="A",
        url="https://rateyourmusic.com/release/single/a/title/", release_type="single")
    monkeypatch.setattr(dataset_mod, "get_chart", lambda path: [album, single])
    monkeypatch.setattr(dataset_mod, "set_delay", lambda sec: None)
    export_chart(out_dir=str(tmp_path))
    assert len(read_dataset(str(tmp_path / "releases.jsonl"))) == 2
