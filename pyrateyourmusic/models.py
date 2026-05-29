"""Data models for rateyourmusic.com objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Track:
    """A single track from a release tracklist."""

    position: str       # "1", "A1", "2.3", ...
    title: str
    duration: str = ""  # raw "4:13" or "" when absent

    def __str__(self) -> str:
        return f"{self.position}. {self.title}".strip(". ")

    @property
    def as_dict(self) -> dict:
        return {"position": self.position, "title": self.title, "duration": self.duration}


@dataclass
class Release:
    """A music release (album / EP / single) as scraped from RYM.

    ``rym_id`` is the canonical ``<artist>/<title>`` slug, e.g.
    ``"radiohead/ok-computer"`` — the stable anchor for cross-linking.
    """

    rym_id: str                     # "<artist>/<title>" slug
    title: str
    artist: str
    url: str

    artist_id: str = ""             # artist slug
    release_type: str = "album"     # album / ep / single / comp / ...
    year: Optional[int] = None
    date: str = ""                  # raw release date string
    rating: Optional[float] = None  # average rating 0-5
    n_ratings: Optional[int] = None
    n_reviews: Optional[int] = None
    primary_genres: List[str] = field(default_factory=list)
    secondary_genres: List[str] = field(default_factory=list)
    descriptors: List[str] = field(default_factory=list)
    tracklist: List[Track] = field(default_factory=list)
    cover_url: str = ""

    def __str__(self) -> str:
        y = f" ({self.year})" if self.year else ""
        return f"{self.artist} - {self.title}{y}"

    @property
    def genres(self) -> List[str]:
        """Primary then secondary genres, de-duplicated, order preserved."""
        out: List[str] = []
        for g in self.primary_genres + self.secondary_genres:
            if g not in out:
                out.append(g)
        return out

    @property
    def track_count(self) -> int:
        return len(self.tracklist)

    @property
    def as_dict(self) -> dict:
        return {
            "rym_id": self.rym_id,
            "title": self.title,
            "artist": self.artist,
            "artist_id": self.artist_id,
            "url": self.url,
            "release_type": self.release_type,
            "year": self.year,
            "date": self.date,
            "rating": self.rating,
            "n_ratings": self.n_ratings,
            "n_reviews": self.n_reviews,
            "primary_genres": self.primary_genres,
            "secondary_genres": self.secondary_genres,
            "descriptors": self.descriptors,
            "tracklist": [t.as_dict for t in self.tracklist],
            "track_count": self.track_count,
            "cover_url": self.cover_url,
        }


@dataclass
class Artist:
    """An artist profile as scraped from an RYM ``/artist/<slug>`` page.

    ``rym_id`` is the artist slug, e.g. ``"radiohead"``.
    """

    rym_id: str                  # artist slug
    name: str
    url: str

    formed: str = ""
    located: str = ""
    members: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    notes: str = ""
    discography: List["ReleaseStub"] = field(default_factory=list)

    def __str__(self) -> str:
        return self.name

    @property
    def release_count(self) -> int:
        return len(self.discography)

    @property
    def as_dict(self) -> dict:
        return {
            "rym_id": self.rym_id,
            "name": self.name,
            "url": self.url,
            "formed": self.formed,
            "located": self.located,
            "members": self.members,
            "aliases": self.aliases,
            "genres": self.genres,
            "related": self.related,
            "notes": self.notes,
            "discography": [r.as_dict for r in self.discography],
            "release_count": self.release_count,
        }


@dataclass
class ReleaseStub:
    """A lightweight release card from a chart, discography, or listing page."""

    rym_id: str
    title: str
    artist: str
    url: str

    artist_id: str = ""
    release_type: str = "album"
    year: Optional[int] = None
    date: str = ""
    rating: Optional[float] = None
    n_ratings: Optional[int] = None
    n_reviews: Optional[int] = None
    primary_genres: List[str] = field(default_factory=list)
    secondary_genres: List[str] = field(default_factory=list)
    descriptors: List[str] = field(default_factory=list)
    cover_url: str = ""
    position: Optional[int] = None  # chart rank, when from a chart page

    @property
    def genres(self) -> List[str]:
        """Primary then secondary genres, de-duplicated, order preserved."""
        out: List[str] = []
        for g in self.primary_genres + self.secondary_genres:
            if g not in out:
                out.append(g)
        return out

    def get(self) -> Release:
        """Fetch the full :class:`Release` detail for this card.

        Note: release detail pages are heavily rate-limited; this may raise a
        ``RuntimeError`` (503 origin block) from datacenter IPs.
        """
        from pyrateyourmusic.release import get_release
        return get_release(self.rym_id, release_type=self.release_type)

    def __str__(self) -> str:
        y = f" ({self.year})" if self.year else ""
        return f"{self.artist} - {self.title}{y}"

    @property
    def as_dict(self) -> dict:
        return {
            "rym_id": self.rym_id,
            "title": self.title,
            "artist": self.artist,
            "artist_id": self.artist_id,
            "url": self.url,
            "release_type": self.release_type,
            "year": self.year,
            "date": self.date,
            "rating": self.rating,
            "n_ratings": self.n_ratings,
            "n_reviews": self.n_reviews,
            "primary_genres": self.primary_genres,
            "secondary_genres": self.secondary_genres,
            "descriptors": self.descriptors,
            "cover_url": self.cover_url,
            "position": self.position,
        }
