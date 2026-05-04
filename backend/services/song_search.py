"""
Song search service.
Combines Spotify (track info), Last.fm (plays, similar tracks)
and MusicBrainz (sample relationships).
"""
import asyncio
import os
import logging
import httpx

from .spotify import _get_token

logger = logging.getLogger(__name__)

LASTFM_KEY = os.environ.get("LASTFM_API_KEY", "")

MB_HEADERS = {
    "User-Agent": "SoundCardMusic/1.0 (sebastianpomi@gmail.com)",
    "Accept": "application/json",
}


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
# MusicBrainz — sample relationships
# ---------------------------------------------------------------------------

def _artist_credit_str(credits: list) -> str:
    """Turn a MusicBrainz artist-credit list into a readable string."""
    parts = []
    for c in credits:
        if isinstance(c, str):          # joinphrase separator
            parts.append(c)
        elif isinstance(c, dict):
            # Use credited name if different from canonical
            parts.append(c.get("name") or c.get("artist", {}).get("name", ""))
    return "".join(parts).strip(" ,&")


async def get_musicbrainz_samples(title: str, artist: str) -> dict:
    """
    Look up sample relationships for a recording in MusicBrainz.

    Returns:
        {
          "samples_used":  [{"name": ..., "artist": ..., "year": ...}],  # what this song samples
          "sampled_by":    [{"name": ..., "artist": ..., "year": ...}],  # who sampled this song
          "interpolations":[{"name": ..., "artist": ..., "year": ...}],  # melodic interpolations
          "mb_url": "https://musicbrainz.org/recording/{mbid}"
        }
    """
    try:
        async with httpx.AsyncClient(timeout=12, headers=MB_HEADERS) as client:
            # Step 1: search for the recording
            r = await client.get(
                "https://musicbrainz.org/ws/2/recording",
                params={
                    "query": f'recording:"{title}" AND artist:"{artist}"',
                    "fmt": "json",
                    "limit": 5,
                },
            )
            if r.status_code != 200:
                return {}

            recordings = r.json().get("recordings", [])
            if not recordings:
                return {}

            # Pick highest-scored result
            recordings.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
            mbid = recordings[0]["id"]

            # MusicBrainz rate limit: 1 req/sec
            await asyncio.sleep(1.1)

            # Step 2: fetch the recording with its recording relationships
            r2 = await client.get(
                f"https://musicbrainz.org/ws/2/recording/{mbid}",
                params={"inc": "recording-rels+artist-credits", "fmt": "json"},
            )
            if r2.status_code != 200:
                return {}

            relations = r2.json().get("relations", [])

    except Exception as e:
        logger.warning(f"MusicBrainz sample lookup failed for '{title}': {e}")
        return {}

    samples_used   = []  # this song SAMPLES from another
    sampled_by     = []  # this song HAS BEEN SAMPLED by another
    interpolations = []  # melodic interpolation (in or out)

    for rel in relations:
        rel_type  = rel.get("type", "")
        direction = rel.get("direction", "forward")  # "forward" or "backward"
        target    = rel.get("recording", {})
        if not target:
            continue

        target_title  = target.get("title", "")
        target_year   = (target.get("first-release-date") or "")[:4]
        target_artist = _artist_credit_str(target.get("artist-credit", []))

        entry = {"name": target_title, "artist": target_artist, "year": target_year}

        if rel_type == "samples material":
            # forward  → this recording samples the target
            # backward → the target samples this recording
            if direction == "forward":
                samples_used.append(entry)
            else:
                sampled_by.append(entry)

        elif rel_type == "interpolates":
            interpolations.append(entry)

        elif rel_type == "has samples":
            # Some MB entries use "has samples" (reverse of "samples material")
            if direction == "backward":
                samples_used.append(entry)
            else:
                sampled_by.append(entry)

    return {
        "samples_used":   samples_used,
        "sampled_by":     sampled_by,
        "interpolations": interpolations,
        "mb_url": f"https://musicbrainz.org/recording/{mbid}",
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def get_song_data(query: str) -> dict:
    """
    Combine Spotify + Last.fm + MusicBrainz data for a track query.
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
    artist_spotify_url = artists_raw[0].get("external_urls", {}).get("spotify") if artists_raw else None

    # --- Run Last.fm + MusicBrainz in parallel ---
    lfm_info, lfm_similar, mb_samples = await asyncio.gather(
        get_lastfm_track_info(title, artist_name),
        get_lastfm_similar_tracks(title, artist_name),
        get_musicbrainz_samples(title, artist_name),
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
        # MusicBrainz samples
        "samples_used":   mb_samples.get("samples_used", []),
        "sampled_by":     mb_samples.get("sampled_by", []),
        "interpolations": mb_samples.get("interpolations", []),
        "mb_url":         mb_samples.get("mb_url", ""),
    }
