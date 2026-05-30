"""Release detail fetching for rateyourmusic.com.

Release detail pages (``/release/<type>/<artist>/<title>/``) carry the full
tracklist plus genres, descriptors and ratings. They are the most heavily
rate-limited surface on RYM and frequently answer a 503 origin block from
datacenter IPs.

Fallback chain for :func:`get_release`:

1. **Live fetch** via FlareSolverr — succeeds from residential IPs; 503s from
   datacenter IPs.
2. **Wayback Machine** — if the live fetch raises a ``RuntimeError`` (503 block),
   ``unblock_requests.wayback_html`` is tried. Wayback snapshots are stale (often
   months old) but cover title, artist, tracklist, rating and cover reliably.
3. **RuntimeError** — re-raised with clear guidance when both paths fail.

Chart and artist pages are not affected; they carry the same metadata fields and
remain reachable without this fallback.
"""
from __future__ import annotations

import logging

from pyrateyourmusic._parse import parse_release_page
from pyrateyourmusic.models import Release, Track
from pyrateyourmusic.transport import BASE_URL, get_html

logger = logging.getLogger(__name__)


def _build_release(html: str, rym_id: str) -> Release:
    raw = parse_release_page(html, rym_id)
    tracks = [Track(position=p, title=t, duration=d) for p, t, d in raw.pop("tracklist")]
    return Release(**raw, tracklist=tracks)


def get_release(rym_id: str, release_type: str = "album") -> Release:
    """Fetch and parse a release detail page.

    Applies a three-step fallback chain:

    1. Live fetch via FlareSolverr.
    2. Wayback Machine snapshot (stale, but recovers title/tracklist/rating).
    3. Raises ``RuntimeError`` with guidance when both fail.

    Args:
        rym_id: Canonical ``<artist>/<title>`` slug, e.g.
            ``"radiohead/ok-computer"``.
        release_type: URL type segment (``album``, ``ep``, ``single``, ...).

    Returns:
        A :class:`~pyrateyourmusic.models.Release`. Fields sourced from Wayback
        may be incomplete (genres/descriptors are often absent in older snapshots).

    Raises:
        RuntimeError: when both live and Wayback fetches fail.
    """
    rym_id = rym_id.strip("/")
    path = f"/release/{release_type}/{rym_id}/"
    url = f"{BASE_URL}{path}"

    # 1. Live fetch
    try:
        html = get_html(path)
        return _build_release(html, rym_id)
    except RuntimeError as live_err:
        logger.warning("Live fetch blocked (503) for %s — trying Wayback", url)
        _live_err = live_err

    # 2. Wayback Machine fallback
    try:
        from unblock_requests import wayback_html  # type: ignore
        html = wayback_html(url)
        if html:
            logger.info("Serving %s from Wayback Machine (stale snapshot)", url)
            return _build_release(html, rym_id)
    except Exception as wb_err:
        logger.warning("Wayback fetch failed for %s: %s", url, wb_err)

    # 3. Both failed
    raise RuntimeError(
        f"rateyourmusic.com release detail unavailable for {url}. "
        "Live fetch returned a 503 origin block and the Wayback Machine "
        "snapshot could not be retrieved. "
        "Retry later from a residential IP, or use chart/artist data "
        "(which carry the same metadata fields and remain reachable)."
    ) from _live_err
