"""pyrateyourmusic — Python HTML scraper for rateyourmusic.com.

rateyourmusic.com (RYM / Sonemic) is a community music database with ratings,
genre taxonomy, descriptors and discographies. This scraper parses HTML pages
and returns typed dataclasses for releases and artists, plus their charts.
CSS selectors are best-effort and may need updating if RYM changes its markup.

RYM sits behind a heavy interactive Cloudflare deployment, so a **FlareSolverr**
proxy is required — point ``PYRATEYOURMUSIC_FLARESOLVERR_URL`` at one. Release
*detail* pages are additionally rate-limited at the origin and may return 503
from datacenter IPs; chart and artist pages carry the same metadata and remain
reachable.

The canonical anchor (``rym_id``) is the URL slug: ``<artist>/<title>`` for a
release (``"radiohead/ok-computer"``) and ``<slug>`` for an artist
(``"radiohead"``).
"""
from pyrateyourmusic.artist import get_artist, get_discography
from pyrateyourmusic.charts import get_chart, top_albums
from pyrateyourmusic.ids import artist_to_extra, release_to_extra
from pyrateyourmusic.models import Artist, Release, ReleaseStub, Track
from pyrateyourmusic.release import get_release
from pyrateyourmusic.transport import (
    flaresolverr_url,
    reset_session,
    set_delay,
    set_solve_timeout,
)
from pyrateyourmusic.version import __version__

__all__ = [
    "Artist",
    "Release",
    "ReleaseStub",
    "Track",
    "get_artist",
    "get_chart",
    "get_discography",
    "get_release",
    "top_albums",
    "artist_to_extra",
    "release_to_extra",
    "flaresolverr_url",
    "reset_session",
    "set_delay",
    "set_solve_timeout",
    "__version__",
]
