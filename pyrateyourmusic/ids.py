"""Converters from pyrateyourmusic models to flat ``rym_*``-namespaced dicts.

Flattens RYM model objects into plain dicts suitable for use as external-ID
payloads, database records, or cross-linking metadata. The ``rym_*`` keys become
canonical-ID anchors for cross-linking releases and artists.

Key namespace
-------------
Release:
    ``rym_id``              — canonical ``<artist>/<title>`` slug (anchor)
    ``rym_url``             — canonical release page URL
    ``rym_title``
    ``rym_artist``
    ``rym_artist_id``       — artist slug
    ``rym_type``            — release type (album / ep / single / ...)
    ``rym_year``            — int year
    ``rym_date``            — raw release date string
    ``rym_rating``          — average rating 0-5 (str)
    ``rym_n_ratings``       — number of ratings (str)
    ``rym_n_reviews``       — number of reviews (str)
    ``rym_primary_genres``  — JSON array
    ``rym_secondary_genres``— JSON array
    ``rym_descriptors``     — JSON array
    ``rym_cover``           — cover-art URL

Artist:
    ``rym_artist_id``       — artist slug (anchor)
    ``rym_artist_url``      — canonical artist page URL
    ``rym_artist_name``
    ``rym_formed``
    ``rym_located``
    ``rym_genres``          — JSON array
    ``rym_aliases``         — JSON array
    ``rym_members``         — JSON array
    ``rym_related``         — JSON array
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pyrateyourmusic.models import Artist, Release, ReleaseStub


def release_to_extra(release: "Union[Release, ReleaseStub]") -> dict:
    """Convert a Release or ReleaseStub to a flat ``rym_*``-keyed dict."""
    extra: dict = {
        "rym_id": release.rym_id,
        "rym_release_key": release.release_key,
        "rym_url": release.url,
        "rym_title": release.title,
    }
    if release.artist:
        extra["rym_artist"] = release.artist
    if release.artist_id:
        extra["rym_artist_id"] = release.artist_id
    if release.release_type:
        extra["rym_type"] = release.release_type
    if release.year is not None:
        extra["rym_year"] = str(release.year)
    if release.date:
        extra["rym_date"] = release.date
    if release.rating is not None:
        extra["rym_rating"] = str(release.rating)
    if release.n_ratings is not None:
        extra["rym_n_ratings"] = str(release.n_ratings)
    if release.n_reviews is not None:
        extra["rym_n_reviews"] = str(release.n_reviews)
    if release.primary_genres:
        extra["rym_primary_genres"] = json.dumps(release.primary_genres, ensure_ascii=False)
    if release.secondary_genres:
        extra["rym_secondary_genres"] = json.dumps(release.secondary_genres, ensure_ascii=False)
    if release.descriptors:
        extra["rym_descriptors"] = json.dumps(release.descriptors, ensure_ascii=False)
    if release.cover_url:
        extra["rym_cover"] = release.cover_url
    return extra


def artist_to_extra(artist: "Artist") -> dict:
    """Convert an :class:`~pyrateyourmusic.models.Artist` to an ``extra`` dict."""
    extra: dict = {
        "rym_artist_id": artist.rym_id,
        "rym_artist_url": artist.url,
        "rym_artist_name": artist.name,
    }
    if artist.formed:
        extra["rym_formed"] = artist.formed
    if artist.located:
        extra["rym_located"] = artist.located
    if artist.genres:
        extra["rym_genres"] = json.dumps(artist.genres, ensure_ascii=False)
    if artist.aliases:
        extra["rym_aliases"] = json.dumps(artist.aliases, ensure_ascii=False)
    if artist.members:
        extra["rym_members"] = json.dumps(artist.members, ensure_ascii=False)
    if artist.related:
        extra["rym_related"] = json.dumps(artist.related, ensure_ascii=False)
    return extra
