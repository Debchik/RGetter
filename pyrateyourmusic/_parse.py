"""HTML parsers for rateyourmusic.com pages.

Three page shapes are parsed:

- **Chart listing** (``/charts/...``) — a stack of
  ``.page_charts_section_charts_item`` blocks, each carrying title, artist,
  date, average rating, rating/review counts, primary/secondary genres and
  descriptors inline. This is the reliable bulk source.
- **Artist** (``/artist/<slug>``) — header name, an ``.artist_info`` fact table
  (formed, members, aliases, genres, related artists, notes) and a
  ``.disco_release`` discography with per-release year and rating.
- **Release detail** (``/release/album/<artist>/<title>/``) — the classic
  ``.album_title`` / ``.album_info`` layout with tracklist. These pages are
  heavily rate-limited and may be unreachable; the parser is tolerant.

Every field is optional: missing markup yields an empty/default value rather
than an exception.
"""
from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pyrateyourmusic._clean import (
    artist_slug_from_url,
    clean,
    parse_count,
    parse_rating,
    parse_year,
    release_slug_from_url,
    release_type_from_url,
)

BASE_URL = "https://rateyourmusic.com"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _abs(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urljoin(BASE_URL + "/", url)


def _texts(els) -> List[str]:
    out: List[str] = []
    for el in els:
        t = clean(el.get_text(" "))
        if t and t not in out:
            out.append(t)
    return out


# --------------------------------------------------------------------------- #
# Chart listing
# --------------------------------------------------------------------------- #

def parse_chart(html: str) -> List[dict]:
    """Parse a charts page into a list of release-stub dicts.

    Each dict matches the :class:`~pyrateyourmusic.models.ReleaseStub` fields.
    """
    soup = _soup(html)
    out: List[dict] = []
    items = soup.select(".page_charts_section_charts_item")
    for idx, item in enumerate(items, 1):
        rec = _parse_chart_item(item)
        if not rec:
            continue
        rec.setdefault("position", idx)
        out.append(rec)
    return out


def _parse_chart_item(item) -> Optional[dict]:
    link = item.select_one("a.page_charts_section_charts_item_link.release") or \
        item.select_one("a.page_charts_section_charts_item_link")
    if not link:
        link = item.select_one("a[href*='/release/']")
    if not link or not link.get("href"):
        return None
    url = _abs(link["href"])
    rym_id = release_slug_from_url(url)
    if not rym_id:
        return None

    title = clean(link.get_text(" "))

    credited = item.select_one(".page_charts_section_charts_item_credited_links_primary") \
        or item.select_one(".page_charts_section_charts_item_credited_text")
    artist_a = item.select_one(".page_charts_section_charts_item_credited_links_primary a.artist") \
        or item.select_one("a.artist")
    # The credited block carries the full collaborator string ("A & B"); the
    # first artist anchor supplies the canonical artist_id slug.
    artist = clean(credited.get_text(" ")) if credited else (
        clean(artist_a.get_text(" ")) if artist_a else "")
    artist_id = artist_slug_from_url(_abs(artist_a["href"])) if artist_a and artist_a.get("href") else ""

    date_el = item.select_one(".page_charts_section_charts_item_title_date_compact span") \
        or item.select_one(".page_charts_section_charts_item_date span")
    date = clean(date_el.get_text(" ")) if date_el else ""

    rtype_el = item.select_one(".page_charts_section_charts_item_release_type")
    release_type = clean(rtype_el.get_text()).lower() if rtype_el else release_type_from_url(url)

    primary = _texts(item.select(".page_charts_section_charts_item_genres_primary a.genre"))
    secondary = _texts(item.select(".page_charts_section_charts_item_genres_secondary a.genre"))
    descriptors = _texts(item.select(
        ".page_charts_section_charts_item_genre_descriptors span,"
        " .page_charts_section_charts_item_genre_descriptors a"
    ))

    rating_el = item.select_one(".page_charts_section_charts_item_details_average_num")
    rating = parse_rating(rating_el.get_text()) if rating_el else None
    nr_el = item.select_one(".page_charts_section_charts_item_details_ratings .abbr") \
        or item.select_one(".page_charts_section_charts_item_details_ratings")
    n_ratings = parse_count(nr_el.get_text()) if nr_el else None
    nrev_el = item.select_one(".page_charts_section_charts_item_details_reviews .abbr")
    n_reviews = parse_count(nrev_el.get_text()) if nrev_el else None

    cover = ""
    img = item.select_one(".page_charts_section_charts_item_image img")
    if img:
        cover = _abs(img.get("src") or "")

    return {
        "rym_id": rym_id,
        "title": title,
        "artist": artist,
        "url": url,
        "artist_id": artist_id,
        "release_type": release_type or "album",
        "year": parse_year(date),
        "date": date,
        "rating": rating,
        "n_ratings": n_ratings,
        "n_reviews": n_reviews,
        "primary_genres": primary,
        "secondary_genres": secondary,
        "descriptors": descriptors,
        "cover_url": cover,
    }


# --------------------------------------------------------------------------- #
# Artist page
# --------------------------------------------------------------------------- #

_ARTIST_INFO_KEYS = {
    "formed": "formed",
    "born": "formed",
    "located": "located",
    "currently": "located",
    "members": "members",
    "member": "members",
    "also known as": "aliases",
    "aka": "aliases",
    "related artists": "related",
    "genres": "genres",
    "genre": "genres",
    "notes": "notes",
}


def _dedup(parts: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for p in (clean(x) for x in parts):
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out


def _list_field(val, members: bool = False) -> List[str]:
    """Split an artist-info value into a clean list.

    For ``members``, the page text carries instrument roles in parentheses
    ("Thom Yorke (vocals, guitar)") whose inner commas must not split items, so
    the anchor texts (bare names) are preferred. For other fields the full text
    is split on commas/slashes so bare (non-linked) values are not dropped.
    """
    anchors = [clean(a.get_text(" ")) for a in val.select("a")]
    if members:
        if anchors:
            return _dedup(anchors)
        # no anchors: split on commas that sit outside parentheses
        text = clean(val.get_text(" "))
        parts = re.split(r",(?![^(]*\))", text)
        return _dedup(parts)
    text = clean(val.get_text(" "))
    parts = [p for p in re.split(r"\s*[,/]\s*", text) if clean(p)]
    return _dedup(parts or anchors)


def parse_artist_page(html: str, slug: str) -> dict:
    """Parse an artist page into a raw dict matching the Artist dataclass
    (``discography`` is a list of release-stub dicts).
    """
    soup = _soup(html)

    name = ""
    h1 = soup.select_one("h1.artist_name_hdr") or soup.find("h1")
    if h1:
        name = clean(h1.get_text(" "))

    info = {"formed": "", "located": "", "members": [], "aliases": [],
            "genres": [], "related": [], "notes": ""}
    box = soup.select_one(".artist_info")
    if box:
        for hdr in box.select(".info_hdr"):
            key = clean(hdr.get_text()).lower()
            field = _ARTIST_INFO_KEYS.get(key)
            if not field:
                for k, dest in _ARTIST_INFO_KEYS.items():
                    if k in key:
                        field = dest
                        break
            if not field:
                continue
            val = hdr.find_next_sibling()
            if not val:
                continue
            if field in ("members", "aliases", "related", "genres"):
                info[field] = _list_field(val, members=(field == "members"))
            else:
                info[field] = clean(val.get_text(" "))

    disco = _parse_discography(soup, slug)

    return {
        "rym_id": slug,
        "name": name,
        "url": f"{BASE_URL}/artist/{slug}",
        "formed": info["formed"],
        "located": info["located"],
        "members": info["members"],
        "aliases": info["aliases"],
        "genres": info["genres"],
        "related": info["related"],
        "notes": info["notes"],
        "discography": disco,
    }


def _parse_discography(soup: BeautifulSoup, artist_slug: str) -> List[dict]:
    out: List[dict] = []
    seen = set()
    artist_name = ""
    h1 = soup.select_one("h1.artist_name_hdr") or soup.find("h1")
    if h1:
        artist_name = clean(h1.get_text(" "))

    for row in soup.select(".disco_release"):
        a = row.select_one("a.album") or row.select_one("a[href*='/release/']")
        if not a or not a.get("href"):
            continue
        url = _abs(a["href"])
        rym_id = release_slug_from_url(url)
        if not rym_id or rym_id in seen:
            continue
        seen.add(rym_id)
        title = clean(a.get_text(" ")) or (a.get("title") and clean(a["title"])) or ""
        year_el = row.select_one(".disco_year_ymd, .disco_year")
        date = clean(year_el.get("title")) if year_el and year_el.get("title") else (
            clean(year_el.get_text()) if year_el else "")
        year = parse_year(clean(year_el.get_text())) if year_el else parse_year(date)
        rating_el = row.select_one(".disco_avg_rating")
        rating = parse_rating(rating_el.get_text()) if rating_el else None
        nr_el = row.select_one(".disco_ratings")
        n_ratings = parse_count(nr_el.get_text()) if nr_el else None
        nrev_el = row.select_one(".disco_reviews")
        n_reviews = parse_count(nrev_el.get_text()) if nrev_el else None
        cover = ""
        img = row.select_one("img.image_release")
        if img:
            cover = _abs(img.get("src") or "")
        out.append({
            "rym_id": rym_id,
            "title": title,
            "artist": artist_name,
            "url": url,
            "artist_id": artist_slug,
            "release_type": release_type_from_url(url),
            "year": year,
            "date": date,
            "rating": rating,
            "n_ratings": n_ratings,
            "n_reviews": n_reviews,
            "primary_genres": [],
            "secondary_genres": [],
            "descriptors": [],
            "cover_url": cover,
            "position": None,
        })
    return out


# --------------------------------------------------------------------------- #
# Release detail page
# --------------------------------------------------------------------------- #

def parse_release_page(html: str, rym_id: str) -> dict:
    """Parse a release detail page into a raw dict matching the Release
    dataclass (``tracklist`` is a list of (position, title, duration) tuples).
    """
    soup = _soup(html)

    title_el = soup.select_one(".album_title")
    title = ""
    artist = ""
    artist_id = ""
    if title_el:
        # the artist link sits inside .album_title under .album_artist / span
        artist_a = title_el.select_one("a.artist") or title_el.select_one("span.album_artist a")
        if artist_a:
            artist = clean(artist_a.get_text(" "))
            artist_id = artist_slug_from_url(_abs(artist_a.get("href", "")))
        # title text is the leading text node before the "By <artist>" span
        raw = clean(title_el.get_text(" "))
        title = clean(re.split(r"\bBy\b", raw)[0]) if raw else ""
    if not artist:
        a = soup.select_one(".album_info a.artist, a.artist")
        if a:
            artist = clean(a.get_text(" "))
            artist_id = artist_slug_from_url(_abs(a.get("href", "")))

    info = _parse_release_info(soup)
    tracklist = _parse_tracklist(soup)

    cover = ""
    img = soup.select_one("img.coverart_img, .page_release_art_frame img, #coverart_img")
    if img:
        cover = _abs(img.get("src") or "")

    return {
        "rym_id": rym_id,
        "title": title or info.get("title", ""),
        "artist": artist,
        "artist_id": artist_id,
        "url": f"{BASE_URL}/release/{info.get('release_type', 'album')}/{rym_id}/",
        "release_type": info.get("release_type", "album"),
        "year": info.get("year"),
        "date": info.get("date", ""),
        "rating": info.get("rating"),
        "n_ratings": info.get("n_ratings"),
        "n_reviews": info.get("n_reviews"),
        "primary_genres": info.get("primary_genres", []),
        "secondary_genres": info.get("secondary_genres", []),
        "descriptors": info.get("descriptors", []),
        "tracklist": tracklist,
        "cover_url": cover,
    }


def _parse_release_info(soup: BeautifulSoup) -> dict:
    info: dict = {"primary_genres": [], "secondary_genres": [], "descriptors": []}

    table = soup.select_one("table.album_info")
    if table:
        for row in table.select("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            key = clean(th.get_text()).lower()
            if "primary" in key and "genre" in key:
                info["primary_genres"] = _texts(td.select("a.genre")) or _split_list(td)
            elif "secondary" in key and "genre" in key:
                info["secondary_genres"] = _texts(td.select("a.genre")) or _split_list(td)
            elif "genre" in key and not info["primary_genres"]:
                info["primary_genres"] = _texts(td.select("a.genre")) or _split_list(td)
            elif "descriptor" in key:
                info["descriptors"] = _split_list(td)
            elif "type" in key:
                info["release_type"] = clean(td.get_text()).lower().split()[0] if td.get_text().strip() else "album"
            elif "released" in key or "release date" in key or key == "released":
                info["date"] = clean(td.get_text())
                info["year"] = parse_year(info["date"])

    # ratings: .avg_rating / .num_ratings
    avg = soup.select_one(".avg_rating, span.avg_rating")
    if avg:
        info["rating"] = parse_rating(avg.get_text())
    num = soup.select_one(".num_ratings, span.num_ratings")
    if num:
        info["n_ratings"] = parse_count(num.get_text())
    return info


def _split_list(td) -> List[str]:
    out = []
    for part in re.split(r"[,•/]", clean(td.get_text(" "))):
        p = clean(part)
        if p:
            out.append(p)
    return out


def _parse_tracklist(soup: BeautifulSoup) -> List[tuple]:
    out: List[tuple] = []
    table = soup.select_one("#tracks, ul#tracks, table#tracks, .tracklist")
    rows = []
    if table:
        rows = table.select("li.track, tr.track, .tracklist_line")
    if not rows:
        rows = soup.select("li.track, .tracklist_line")
    for row in rows:
        num_el = row.select_one(".tracklist_num, .track_num, .num")
        title_el = row.select_one(".tracklist_title .rendered_text, .tracklist_title, .song, .track_name")
        dur_el = row.select_one(".tracklist_duration, .track_duration, .duration")
        position = clean(num_el.get_text()) if num_el else ""
        title = clean(title_el.get_text(" ")) if title_el else ""
        if not title:
            continue
        duration = clean(dur_el.get_text()) if dur_el else ""
        out.append((position, title, duration))
    return out
