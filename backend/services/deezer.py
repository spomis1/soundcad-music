import unicodedata
import httpx

BASE_URL = "https://api.deezer.com"


def _normalize(s: str) -> str:
    return unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode().strip()


async def get_top_tracks_with_preview(artist_name: str, limit: int = 5) -> list[dict]:
    """
    Fetch top tracks with 30-second preview URLs from Deezer.
    No API key required. Returns [] on any error.
    Each track: { name, popularity, preview_url, deezer_url }
    """
    async with httpx.AsyncClient(timeout=10) as client:
        # 1. Find artist
        try:
            r = await client.get(
                f"{BASE_URL}/search/artist",
                params={"q": artist_name, "limit": 5, "output": "json"},
            )
            if r.status_code != 200:
                return []
            artists = r.json().get("data", [])
        except Exception:
            return []

        if not artists:
            return []

        # Pick best match by name
        norm_name = _normalize(artist_name)
        artist = None
        for a in artists:
            if _normalize(a.get("name", "")) == norm_name:
                artist = a
                break
        if not artist:
            artist = artists[0]

        artist_id = artist["id"]

        # 2. Get top tracks
        try:
            r2 = await client.get(
                f"{BASE_URL}/artist/{artist_id}/top",
                params={"limit": limit * 2},  # fetch extra in case some have no preview
            )
            if r2.status_code != 200:
                return []
            tracks = r2.json().get("data", [])
        except Exception:
            return []

    results = []
    for t in tracks:
        preview = t.get("preview")  # 30s MP3 URL, always present on Deezer
        if not preview:
            continue
        results.append({
            "name": t.get("title", ""),
            "popularity": t.get("rank", 0) // 10000,  # Deezer rank 0-1M → normalize to 0-100
            "preview_url": preview,
            "deezer_url": t.get("link"),
            "album_cover": t.get("album", {}).get("cover_medium"),
        })
        if len(results) >= limit:
            break
    return results
