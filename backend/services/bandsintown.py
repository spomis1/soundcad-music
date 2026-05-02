import logging
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://rest.bandsintown.com"
APP_ID = "soundcard-music"

# NOTE: Bandsintown's public v3 API was restricted in 2024 and now requires
# approved access. Calls return 403. The service is kept as a no-op so we
# can re-enable it if access is restored or replaced with another source.


async def get_upcoming_events(artist_name: str) -> list[dict]:
    """
    Fetch upcoming events from Bandsintown.
    Currently returns empty due to API access restrictions (HTTP 403).
    Ticketmaster covers global events as primary source.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"{BASE_URL}/artists/{httpx.URL(artist_name).path}/events",
                params={"app_id": APP_ID, "date": "upcoming"},
            )
            if r.status_code == 403:
                logger.debug("Bandsintown API access denied (403) — using Ticketmaster only")
                return []
            if r.status_code != 200:
                return []
            events = r.json()
            if not isinstance(events, list):
                return []
        except Exception:
            return []

    results = []
    for ev in events:
        venue = ev.get("venue", {})
        lat = float(venue.get("latitude") or 0)
        lon = float(venue.get("longitude") or 0)
        results.append({
            "name": ev.get("title") or f"{artist_name} live",
            "date": (ev.get("datetime") or "")[:10],  # ISO → YYYY-MM-DD
            "venue_name": venue.get("name", ""),
            "city": venue.get("city", ""),
            "country": venue.get("country", ""),
            "country_code": venue.get("country", "")[:2].upper(),
            "lat": lat,
            "lon": lon,
            "ticket_url": ev.get("offers", [{}])[0].get("url") if ev.get("offers") else None,
            "estimated_capacity": 1000,
            "min_price": None,
            "max_price": None,
            "currency": "USD",
        })
    return results
