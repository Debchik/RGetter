"""Release detail fetching for rateyourmusic.com.

Release detail pages (``/release/<type>/<artist>/<title>/``) carry the full
tracklist plus genres, descriptors and ratings. They are the most heavily
rate-limited surface on RYM and frequently answer a 503 origin block from
datacenter IPs — :func:`get_release` raises ``RuntimeError`` in that case.
"""
from __future__ import annotations

from pyrateyourmusic._parse import parse_release_page
from pyrateyourmusic.models import Release, Track
from pyrateyourmusic.transport import get_html


def _build_release(html: str, rym_id: str) -> Release:
    raw = parse_release_page(html, rym_id)
    tracks = [Track(position=p, title=t, duration=d) for p, t, d in raw.pop("tracklist")]
    return Release(**raw, tracklist=tracks)


def get_release(rym_id: str, release_type: str = "album") -> Release:
    """Fetch and parse a release detail page.

    Args:
        rym_id: Canonical ``<artist>/<title>`` slug, e.g.
            ``"radiohead/ok-computer"``.
        release_type: URL type segment (``album``, ``ep``, ``single``, ...).

    Returns:
        A fully populated :class:`~pyrateyourmusic.models.Release`.

    Raises:
        RuntimeError: when RYM answers a 503 origin block (common for detail
            pages from datacenter IPs).
    """
    rym_id = rym_id.strip("/")
    html = get_html(f"/release/{release_type}/{rym_id}/")
    return _build_release(html, rym_id)
