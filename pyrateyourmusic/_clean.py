"""Data cleaning utilities for scraped rateyourmusic.com content."""
from __future__ import annotations

import html
import re
import unicodedata
from typing import Optional
from urllib.parse import urlparse


def clean(text: str) -> str:
    """Unescape HTML entities, normalise unicode, collapse whitespace, strip."""
    if not text:
        return ""
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_or_none(text: str) -> Optional[str]:
    val = clean(text)
    if not val or val.lower() in ("none", "n/a", "-", "unknown"):
        return None
    return val


def parse_year(text: str) -> Optional[int]:
    """Extract a 4-digit release year from a date string."""
    m = re.search(r"\b(19|20)\d{2}\b", text or "")
    return int(m.group()) if m else None


def parse_rating(text: str) -> Optional[float]:
    """Parse an RYM average rating ('4.38' or '4.38 / 5') to a float 0-5."""
    m = re.search(r"(\d\.\d{1,2})", (text or "").strip())
    return float(m.group(1)) if m else None


def parse_count(text: str) -> Optional[int]:
    """Parse an RYM count, expanding compact suffixes: '106k' -> 106000,
    '1.2k' -> 1200, '49,576' -> 49576, '2m' -> 2000000.
    """
    if not text:
        return None
    t = clean(text).lower().replace(",", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*([km]?)", t)
    if not m:
        return None
    num = float(m.group(1))
    suffix = m.group(2)
    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000
    return int(round(num))


def release_slug_from_url(url: str) -> str:
    """Extract the canonical ``<artist>/<title>`` slug from a release URL.

    ``/release/album/radiohead/ok-computer/`` -> ``"radiohead/ok-computer"``.
    """
    if not url:
        return ""
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 4 and parts[0] == "release":
        # release / <type> / <artist> / <title>
        return f"{parts[2]}/{parts[3]}"
    return ""


def release_type_from_url(url: str) -> str:
    """Extract the release type segment ('album', 'ep', ...) from a release URL."""
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "release":
        return parts[1]
    return "album"


def artist_slug_from_url(url: str) -> str:
    """Extract the artist slug from an ``/artist/<slug>`` URL."""
    if not url:
        return ""
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "artist":
        return parts[1]
    return parts[-1] if parts else ""


def genre_slug_from_url(url: str) -> str:
    """Extract the genre slug from a ``/genre/<slug>/`` URL."""
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "genre":
        return parts[1]
    return ""
