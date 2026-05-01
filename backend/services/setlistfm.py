import os
import httpx
from datetime import datetime
from typing import Optional

BASE_URL = "https://api.setlist.fm/rest/1.0"
HEADERS = {
    "x-api-key": "",  # set at runtime from env
    "Accept": "application/json",
}


def _headers() -> dict:
    return {**HEADERS, "x-api-key": os.environ["SETLISTFM_API_KEY"]}


async def search_artist(artist_name: str) -> Optional[str]:
    """Returns the setlist.fm artist mbid."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/search/artists",
            headers=_headers(),
            params={"artistName": artist_name, "p": 1, "sort": "relevance"},
        )
        if r.status_code != 200:
            return None
        data = r.json()
        artists = data.get("artist", [])
        if not artists:
            return None
        return artists[0].get("mbid")


async def get_setlists(artist_name: str, max_pages: int = 5) -> list[dict]:
    """Fetch all available setlists for an artist (paginated)."""
    mbid = await search_artist(artist_name)
    if not mbid:
        return []

    all_setlists = []
    async with httpx.AsyncClient(timeout=15) as client:
        for page in range(1, max_pages + 1):
            r = await client.get(
                f"{BASE_URL}/artist/{mbid}/setlists",
                headers=_headers(),
                params={"p": page},
            )
            if r.status_code != 200:
                break
            data = r.json()
            items = data.get("setlist", [])
            if not items:
                break
            for s in items:
                event_date = s.get("eventDate", "")
                try:
                    parsed_date = datetime.strptime(event_date, "%d-%m-%Y")
                    iso_date = parsed_date.strftime("%Y-%m-%d")
                    year = parsed_date.year
                except ValueError:
                    iso_date = event_date
                    year = None

                venue = s.get("venue", {})
                city = venue.get("city", {})
                all_setlists.append({
                    "date": iso_date,
                    "year": year,
                    "venue_name": venue.get("name"),
                    "venue_id": venue.get("id"),
                    "city": city.get("name"),
                    "country": city.get("country", {}).get("name"),
                    "country_code": city.get("country", {}).get("code"),
                    "lat": float(city.get("coords", {}).get("lat", 0) or 0),
                    "lon": float(city.get("coords", {}).get("long", 0) or 0),
                    "tour_name": s.get("tour", {}).get("name") if s.get("tour") else None,
                    "songs_count": sum(
                        len(set_block.get("song", []))
                        for set_block in s.get("sets", {}).get("set", [])
                    ),
                })
            if len(items) < 20:
                break

    all_setlists.sort(key=lambda x: x["date"], reverse=True)
    return all_setlists


def build_tour_timeline(setlists: list[dict]) -> list[dict]:
    """
    Groups concerts by tour name and year.
    Returns a timeline useful for charting venue progression.
    """
    by_tour: dict[str, list] = {}
    for s in setlists:
        key = s.get("tour_name") or str(s.get("year", "Unknown"))
        by_tour.setdefault(key, []).append(s)

    timeline = []
    for tour, shows in by_tour.items():
        shows.sort(key=lambda x: x["date"])
        timeline.append({
            "tour": tour,
            "start_date": shows[0]["date"],
            "end_date": shows[-1]["date"],
            "show_count": len(shows),
            "countries": list({s["country"] for s in shows if s["country"]}),
            "cities": [s["city"] for s in shows if s["city"]],
        })
    timeline.sort(key=lambda x: x["start_date"])
    return timeline
