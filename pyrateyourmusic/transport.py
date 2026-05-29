"""HTTP transport for rateyourmusic.com via FlareSolverr.

rateyourmusic.com sits behind a heavy, interactive Cloudflare deployment that
rejects plain HTTP clients and TLS-fingerprint impersonation alike. A
**FlareSolverr** proxy that drives a real headless browser is required to obtain
clearance. The transport therefore builds an ``unblock_requests.CloudflareSession``
in FlareSolverr mode, resolving the solver endpoint from
``PYRATEYOURMUSIC_FLARESOLVERR_URL`` (or the ``flaresolverr_url`` kwarg).

Release **detail** pages (``/release/album/<artist>/<title>/``) are additionally
rate-limited at the origin and frequently answer ``503`` from datacenter IPs;
artist pages and chart listings are reliably reachable and carry the same
title / artist / year / rating / genre data inline.

Requests are throttled (default 2.0 s) to stay polite.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

BASE_URL = "https://rateyourmusic.com"

_ENV_PREFIX = "PYRATEYOURMUSIC"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL + "/",
}

_session: Optional[Any] = None
_last_request: float = 0.0
_min_delay: float = 2.0
_solve_timeout_ms: int = 120000


def set_delay(seconds: float) -> None:
    """Set the minimum delay between HTTP requests (default: 2.0 s)."""
    global _min_delay
    _min_delay = max(0.0, seconds)


def set_solve_timeout(ms: int) -> None:
    """Set the per-request FlareSolverr solve budget in milliseconds."""
    global _solve_timeout_ms
    _solve_timeout_ms = max(1000, int(ms))
    reset_session()


def flaresolverr_url() -> Optional[str]:
    """Return the configured FlareSolverr endpoint, or ``None``."""
    return os.environ.get(f"{_ENV_PREFIX}_FLARESOLVERR_URL")


def _make_session() -> Any:
    from unblock_requests import CloudflareSession  # type: ignore

    session = CloudflareSession(
        env_prefix=_ENV_PREFIX,
        flaresolverr_timeout_ms=_solve_timeout_ms,
        wayback_fallback=True,
    )
    session.headers.update(_HEADERS)
    return session


def get_session() -> Any:
    global _session
    if _session is None:
        _session = _make_session()
    return _session


def reset_session() -> None:
    global _session
    _session = None


def _throttle() -> None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _min_delay:
        time.sleep(_min_delay - elapsed)
    _last_request = time.time()


def get_html(path: str, params: Optional[dict] = None, timeout: int = 130, **kwargs: Any) -> str:
    """Fetch a page and return the HTML text.

    Args:
        path: Absolute URL or path relative to BASE_URL.
        params: Optional query parameters dict.
        timeout: Per-request timeout in seconds (FlareSolverr solves are slow).

    Returns:
        Response body as a string.

    Raises:
        requests.HTTPError: on a non-2xx HTTP status.
        RuntimeError: when rateyourmusic.com answers a 503 origin block (common
            for ``/release/`` detail pages from datacenter IPs).
    """
    _throttle()
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    resp = get_session().get(url, params=params, timeout=timeout, **kwargs)
    resp.raise_for_status()
    text = resp.text
    if "HTTP ERROR 503" in text and "is currently unable to handle this request" in text:
        raise RuntimeError(
            f"rateyourmusic.com returned a 503 origin block for {url}. "
            "Release detail pages are heavily rate-limited from datacenter IPs; "
            "retry later, slow down (set_delay), or use a residential exit. "
            "Chart and artist pages remain reachable."
        )
    return text
