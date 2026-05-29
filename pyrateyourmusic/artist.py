"""Artist profile fetching for rateyourmusic.com.

Artist pages (``/artist/<slug>``) are reliably reachable and carry the artist
fact table plus a discography of release cards with per-release year and rating.
"""
from __future__ import annotations

from typing import List

from pyrateyourmusic._parse import parse_artist_page
from pyrateyourmusic.models import Artist, ReleaseStub
from pyrateyourmusic.transport import get_html


def _build_artist(html: str, slug: str) -> Artist:
    raw = parse_artist_page(html, slug)
    disco = [ReleaseStub(**d) for d in raw.pop("discography")]
    return Artist(**raw, discography=disco)


def get_artist(slug: str) -> Artist:
    """Fetch and parse an artist page by its RYM slug.

    Args:
        slug: Artist slug as it appears in ``/artist/<slug>``, e.g.
            ``"radiohead"``.

    Returns:
        A fully populated :class:`~pyrateyourmusic.models.Artist`.
    """
    slug = slug.strip("/").split("/")[-1]
    html = get_html(f"/artist/{slug}")
    return _build_artist(html, slug)


def get_discography(slug: str) -> List[ReleaseStub]:
    """Return only the discography release cards for an artist."""
    return get_artist(slug).discography
