import json

from pyrateyourmusic.ids import artist_to_extra, release_to_extra
from pyrateyourmusic.models import Artist, ReleaseStub


def _release() -> ReleaseStub:
    return ReleaseStub(
        rym_id="radiohead/ok-computer",
        title="OK Computer",
        artist="Radiohead",
        url="https://rateyourmusic.com/release/album/radiohead/ok-computer/",
        artist_id="radiohead",
        release_type="album",
        year=1997,
        date="16 June 1997",
        rating=4.23,
        n_ratings=136046,
        n_reviews=694,
        primary_genres=["Alternative Rock", "Art Rock"],
        secondary_genres=["Post-Britpop"],
        descriptors=["melancholic", "anxious"],
        cover_url="https://e.snmc.io/x.jpg",
    )


class TestReleaseToExtra:
    def setup_method(self):
        self.e = release_to_extra(_release())

    def test_anchor(self):
        assert self.e["rym_id"] == "radiohead/ok-computer"

    def test_url(self):
        assert "rateyourmusic.com" in self.e["rym_url"]

    def test_scalars_are_strings(self):
        assert self.e["rym_year"] == "1997"
        assert self.e["rym_rating"] == "4.23"
        assert self.e["rym_n_ratings"] == "136046"

    def test_genres_json(self):
        prim = json.loads(self.e["rym_primary_genres"])
        assert "Art Rock" in prim

    def test_descriptors_json(self):
        desc = json.loads(self.e["rym_descriptors"])
        assert "melancholic" in desc

    def test_artist_id(self):
        assert self.e["rym_artist_id"] == "radiohead"


class TestArtistToExtra:
    def setup_method(self):
        self.a = Artist(
            rym_id="radiohead",
            name="Radiohead",
            url="https://rateyourmusic.com/artist/radiohead",
            formed="1991, Abingdon",
            genres=["Alternative Rock", "Art Rock"],
            aliases=["On a Friday"],
            members=["Thom Yorke"],
        )
        self.e = artist_to_extra(self.a)

    def test_anchor(self):
        assert self.e["rym_artist_id"] == "radiohead"

    def test_name(self):
        assert self.e["rym_artist_name"] == "Radiohead"

    def test_genres_json(self):
        assert "Art Rock" in json.loads(self.e["rym_genres"])

    def test_members_json(self):
        assert "Thom Yorke" in json.loads(self.e["rym_members"])

    def test_no_empty_keys(self):
        assert "rym_located" not in self.e


def test_release_key_is_type_qualified():
    from pyrateyourmusic.models import ReleaseStub
    album = _release()
    single = ReleaseStub(
        rym_id=album.rym_id, title=album.title, artist=album.artist,
        url=album.url.replace("/album/", "/single/"), release_type="single")
    assert album.release_key == "album/radiohead/ok-computer"
    assert single.release_key == "single/radiohead/ok-computer"
    assert release_to_extra(single)["rym_release_key"] != release_to_extra(album)["rym_release_key"]
