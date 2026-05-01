import os
import httpx
from datetime import datetime, timezone

BASE_URL = "https://app.ticketmaster.com/discovery/v2"

# Venue capacity estimates by size category (Ticketmaster doesn't expose raw capacity)
VENUE_SIZE_MAP = {
    "arena": 15000,
    "stadium": 50000,
    "amphitheatre": 10000,
    "amphitheater": 10000,
    "theatre": 2000,
    "theater": 2000,
    "club": 500,
    "bar": 300,
    "festival": 30000,
    "hall": 3000,
    "center": 8000,
    "centre": 8000,
}


def _estimate_capacity(venue_name: str) -> int:
    """Heuristic: guess venue size from its name."""
    if not venue_name:
        return 1000
    lower = venue_name.lower()
    for keyword, cap in VENUE_SIZE_MAP.items():
        if keyword in lower:
            return cap
    return 1000


async def get_upcoming_events(artist_name: str, max_results: int = 20) -> list[dict]:
    """Fetch upcoming events for an artist."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/events.json",
            params={
                "apikey": os.environ["TICKETMASTER_API_KEY"],
                "keyword": artist_name,
                "classificationName": "music",
                "size": max_results,
                "sort": "date,asc",
            },
        )
        if r.status_code != 200:
            return []
        data = r.json()
        events_raw = data.get("_embedded", {}).get("events", [])
        results = []
        for ev in events_raw:
            venue_info = ev.get("_embedded", {}).get("venues", [{}])[0]
            venue_name = venue_info.get("name", "")
            city = venue_info.get("city", {}).get("name", "")
            country = venue_info.get("country", {}).get("name", "")
            country_code = venue_info.get("country", {}).get("countryCode", "")
            location = venue_info.get("location", {})
            date_str = ev.get("dates", {}).get("start", {}).get("localDate", "")
            ticket_url = ev.get("url", "")
            price_ranges = ev.get("priceRanges", [])
            min_price = price_ranges[0].get("min") if price_ranges else None
            max_price = price_ranges[0].get("max") if price_ranges else None
            currency = price_ranges[0].get("currency", "USD") if price_ranges else "USD"
            results.append({
                "name": ev.get("name", ""),
                "date": date_str,
                "venue_name": venue_name,
                "city": city,
                "country": country,
                "country_code": country_code,
                "lat": float(location.get("latitude", 0) or 0),
                "lon": float(location.get("longitude", 0) or 0),
                "ticket_url": ticket_url,
                "estimated_capacity": _estimate_capacity(venue_name),
                "min_price": min_price,
                "max_price": max_price,
                "currency": currency,
            })
        return results
