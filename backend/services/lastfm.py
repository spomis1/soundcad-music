import os
import httpx
from typing import Optional

BASE_URL = "https://ws.audioscrobbler.com/2.0/"


def _params(method: str, **kwargs) -> dict:
    return {"method": method, "api_key": os.environ["LASTFM_API_KEY"], "format": "json", **kwargs}


async def get_artist_info(artist_name: str) -> dict:
    """Basic artist info + listener/playcount stats."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(BASE_URL, params=_params("artist.getinfo", artist=artist_name))
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            return {}
        a = data["artist"]
        return {
            "name": a.get("name"),
            "mbid": a.get("mbid"),
            "listeners": int(a["stats"].get("listeners", 0)),
            "playcount": int(a["stats"].get("playcount", 0)),
            "bio_summary": a.get("bio", {}).get("summary", ""),
            "tags": [t["name"] for t in a.get("tags", {}).get("tag", [])],
            "image_url": next(
                (img["#text"] for img in reversed(a.get("image", [])) if img["#text"]), None
            ),
        }


async def get_artist_top_countries(artist_name: str) -> list[dict]:
    """
    Last.fm doesn't expose per-country breakdown via public API.
    We proxy this with geo.getTopArtists per region for the top countries.
    As an alternative, we return weekly chart data as a global proxy.
    """
    countries = [
        "United States", "United Kingdom", "Germany", "Brazil", "France",
        "Mexico", "Argentina", "Spain", "Australia", "Canada",
        "Japan", "South Korea", "Italy", "Netherlands", "Poland",
        "Sweden", "Russia", "Turkey", "India", "Indonesia",
    ]
    results = []
    async with httpx.AsyncClient(timeout=15) as client:
        for country in countries:
            try:
                r = await client.get(
                    BASE_URL,
                    params=_params("geo.gettopartists", country=country, limit=50),
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                artists = data.get("topartists", {}).get("artist", [])
                for rank, a in enumerate(artists, 1):
                    if a.get("name", "").lower() == artist_name.lower():
                        results.append({"country": country, "rank": rank, "listeners": int(a.get("listeners", 0))})
                        break
            except Exception:
                continue
    return results


async def get_weekly_chart_trend(artist_name: str) -> list[dict]:
    """Fetch the global weekly chart history to see listener trend over time."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(BASE_URL, params=_params("chart.gettopartists", limit=200))
        if r.status_code != 200:
            return []
        data = r.json()
        artists = data.get("artists", {}).get("artist", [])
        for a in artists:
            if a.get("name", "").lower() == artist_name.lower():
                return [{"listeners": int(a.get("listeners", 0)), "playcount": int(a.get("playcount", 0))}]
    return []


async def get_similar_artists(artist_name: str) -> list[dict]:
    """Last.fm similar artists as fallback when Spotify's endpoint is unavailable."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(BASE_URL, params=_params("artist.getsimilar", artist=artist_name, limit=6))
        if r.status_code != 200:
            return []
        data = r.json()
        if "error" in data:
            return []
        artists = data.get("similarartists", {}).get("artist", [])
        clean = [
            {"name": a["name"], "popularity": int(float(a.get("match", 0)) * 100)}
            for a in artists
            if "/" not in a["name"] and "&" not in a["name"] and len(a["name"]) < 50
        ]
        return clean[:6]


async def get_top_artists_global(limit: int = 100) -> list[str]:
    """Used by the weekly cache refresh job."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(BASE_URL, params=_params("chart.gettopartists", limit=limit))
        r.raise_for_status()
        data = r.json()
        return [a["name"] for a in data.get("artists", {}).get("artist", [])]
