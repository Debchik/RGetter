"""Chart listing access for rateyourmusic.com.

Chart pages (``/charts/...``) are the reliable bulk source of release metadata:
each entry carries title, artist, date, average rating, rating/review counts,
and primary/secondary genres + descriptors inline — no detail-page fetch needed.
"""
from __future__ import annotations

from typing import List

from pyrateyourmusic._parse import parse_chart
from pyrateyourmusic.models import ReleaseStub
from pyrateyourmusic.transport import get_html


def _stubs_from_html(html: str) -> List[ReleaseStub]:
    return [ReleaseStub(**rec) for rec in parse_chart(html)]


def get_chart(path: str = "/charts/top/album/all-time/") -> List[ReleaseStub]:
    """Fetch a single chart page and return its release cards.

    Args:
        path: Chart path relative to the site root, e.g.
            ``"/charts/top/album/all-time/"`` or
            ``"/charts/top/album/2023/"``.

    Returns:
        List of :class:`~pyrateyourmusic.models.ReleaseStub` cards, with
        ``position`` set to the in-page rank.
    """
    html = get_html(path)
    return _stubs_from_html(html)


def top_albums(period: str = "all-time") -> List[ReleaseStub]:
    """Convenience wrapper for ``/charts/top/album/<period>/``.

    Args:
        period: ``"all-time"``, a year (``"2023"``), a decade (``"1990s"``), ...
    """
    return get_chart(f"/charts/top/album/{period}/")
