"""
Song search service.
Combines Spotify (track info) and Last.fm (plays, similar tracks).
"""
import asyncio
import os
import logging
import httpx

from .spotify import _get_token

logger = logging.getLogger(__name__)

LASTFM_KEY = os.environ.get("LASTFM_API_KEY", "")


# ---------------------------------------------------------------------------
# Spotify helpers
# ---------------------------------------------------------------------------

async def search_track_spotify(query: str) -> dict | None:
    """Search Spotify for a track. Returns the best match or None."""
    try:
        token = await _get_token()
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://api.spotify.com/v1/search",
            params={"q": query, "type": "track", "limit": 1, "market": "US"},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            logger.warning(f"Spotify search returned {r.status_code} for '{query}'")
            return None
        items = r.json().get("tracks", {}).get("items", [])
        return items[0] if items else None


async def get_artist_spotify_url(artist_id: str) -> str | None:
    """Fetch Spotify URL for an artist id (needed to build artist profile link)."""
    try:
        token = await _get_token()
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"https://api.spotify.com/v1/artists/{artist_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 200:
                return r.json().get("external_urls", {}).get("spotify")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Last.fm helpers
# ---------------------------------------------------------------------------

async def get_lastfm_track_info(title: str, artist: str) -> dict:
    """Fetch Last.fm track.getInfo."""
    if not LASTFM_KEY:
        return {}
    async with httpx.AsyncClient(timeout=8) as client:
        try:
            r = await client.get(
                "https://ws.audioscrobbler.com/2.0/",
                params={
                    "method": "track.getInfo",
                    "api_key": LASTFM_KEY,
                    "artist": artist,
                    "track": title,
                    "format": "json",
                    "autocorrect": 1,
                },
            )
            if r.status_code != 200:
                return {}
            data = r.json().get("track", {})
            tags = [t["name"] for t in data.get("toptags", {}).get("tag", [])[:6]]
            return {
                "listeners": int(data.get("listeners", 0) or 0),
                "playcount": int(data.get("playcount", 0) or 0),
                "tags": tags,
            }
        except Exception as e:
            logger.warning(f"Last.fm track.getInfo failed: {e}")
            return {}


async def get_lastfm_similar_tracks(title: str, artist: str) -> list[dict]:
    """Fetch similar tracks via Last.fm track.getSimilar."""
    if not LASTFM_KEY:
        return []
    async with httpx.AsyncClient(timeout=8) as client:
        try:
            r = await client.get(
                "https://ws.audioscrobbler.com/2.0/",
                params={
                    "method": "track.getSimilar",
                    "api_key": LASTFM_KEY,
                    "artist": artist,
                    "track": title,
                    "format": "json",
                    "limit": 8,
                    "autocorrect": 1,
                },
            )
            if r.status_code != 200:
                return []
            items = r.json().get("similartracks", {}).get("track", [])
            result = []
            for t in items[:8]:
                a = t.get("artist", {})
                result.append({
                    "name": t.get("name", ""),
                    "artist": a.get("name", "") if isinstance(a, dict) else "",
                    "playcount": int(t.get("playcount", 0) or 0),
                })
            return result
        except Exception as e:
            logger.warning(f"Last.fm track.getSimilar failed: {e}")
            return []


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def get_song_data(query: str) -> dict:
    """
    Combine Spotify + Last.fm data for a track query.
    Returns a dict ready for the API response, or empty dict if not found.
    """
    track = await search_track_spotify(query)
    if not track:
        return {}

    # --- Basic info from Spotify ---
    title = track.get("name", "")
    artists_raw = track.get("artists", [])
    artist_name = artists_raw[0]["name"] if artists_raw else ""
    all_artists = [a["name"] for a in artists_raw]
    artist_id = artists_raw[0].get("id") if artists_raw else None

    album = track.get("album", {})
    album_name = album.get("name", "")
    album_images = album.get("images", [])
    cover = album_images[0]["url"] if album_images else None
    release_date = album.get("release_date", "")
    year = release_date[:4] if release_date else ""

    popularity = track.get("popularity", 0)
    preview_url = track.get("preview_url")
    spotify_url = track.get("external_urls", {}).get("spotify")

    # artist Spotify URL (already in the search result)
    artist_spotify_url = artists_raw[0].get("external_urls", {}).get("spotify") if artists_raw else None

    # --- Parallel Last.fm calls ---
    lfm_info, lfm_similar = await asyncio.gather(
        get_lastfm_track_info(title, artist_name),
        get_lastfm_similar_tracks(title, artist_name),
    )

    return {
        "name": title,
        "artist_name": artist_name,
        "all_artists": all_artists,
        "artist_id": artist_id,
        "artist_spotify_url": artist_spotify_url,
        "album_name": album_name,
        "cover": cover,
        "year": year,
        "release_date": release_date,
        "popularity": popularity,
        "preview_url": preview_url,
        "spotify_url": spotify_url,
        # Last.fm
        "lastfm_listeners": lfm_info.get("listeners", 0),
        "lastfm_playcount": lfm_info.get("playcount", 0),
        "tags": lfm_info.get("tags", []),
        "similar_tracks": lfm_similar,
    }
