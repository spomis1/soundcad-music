import unicodedata
import httpx


def _norm(s: str) -> str:
    return unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode().strip()


async def get_itunes_data(artist_name: str) -> dict:
    """
    Fetch Apple Music / iTunes artist data.
    No API key required. Rate limit: ~20 req/min.
    Returns: itunes_url (Apple Music profile link), itunes_genre.
    """
    async with httpx.AsyncClient(timeout=8) as client:
        try:
            r = await client.get(
                "https://itunes.apple.com/search",
                params={
                    "term": artist_name,
                    "entity": "musicArtist",
                    "media": "music",
                    "limit": 5,
                },
            )
            if r.status_code != 200:
                return {}
            results = r.json().get("results", [])
            if not results:
                return {}

            # Prefer exact name match (accent-normalized)
            target = _norm(artist_name)
            best = None
            for item in results:
                if _norm(item.get("artistName", "")) == target:
                    best = item
                    break
            if not best:
                best = results[0]

            return {
                "itunes_url": best.get("artistLinkUrl", ""),
                "itunes_genre": best.get("primaryGenreName", ""),
                "itunes_id": best.get("artistId"),
            }
        except Exception:
            return {}
