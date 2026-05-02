import os
import unicodedata
import httpx
from datetime import datetime, timezone

BASE_URL = "https://app.ticketmaster.com/discovery/v2"

# Venue capacity estimates by size category (Ticketmaster doesn't expose raw capacity)
VENUE_SIZE_MAP = {
    # English
    "arena": 15000, "stadium": 50000, "dome": 40000,
    "amphitheatre": 10000, "amphitheater": 10000,
    "theatre": 2000, "theater": 2000,
    "auditorium": 3000, "hall": 3000,
    "center": 8000, "centre": 8000,
    "festival": 30000, "club": 500, "bar": 300,
    # Spanish / Portuguese
    "estadio": 50000, "palacio": 8000,
    "auditorio": 3000, "teatro": 1500,
    "velodromo": 30000, "recinto": 5000,
    # Catalan
    "estadi": 50000, "palau": 8000,
    # Italian
    "ippodromo": 30000, "stadio": 50000, "unipol": 15000,
    # French
    "stade": 50000, "velodrome": 30000, "zenith": 6000, "accor": 20000,
    # German / Dutch / Polish / Nordic
    "stadion": 50000, "narodowy": 50000,
    "gelredome": 30000, "ziggo": 17000,
    # UK / Ireland
    "wembley": 90000, "emirates": 60000, "aviva": 51000, "murrayfield": 67000,
    # Generic large
    "olimpic": 50000, "olympic": 50000, "national": 40000,
    "coliseum": 20000, "colosseum": 20000, "o2": 20000,
}

# Country code → default currency
_COUNTRY_CURRENCY = {
    "GB": "GBP", "AU": "AUD", "CA": "CAD", "JP": "JPY",
    "MX": "MXN", "BR": "BRL", "AR": "ARS", "CL": "CLP",
    "CO": "COP", "PE": "PEN", "KR": "KRW", "IN": "INR",
    "SE": "SEK", "NO": "NOK", "DK": "DKK", "CH": "CHF",
    "PL": "PLN", "CZ": "CZK", "HU": "HUF", "RO": "RON",
    "NZ": "NZD", "ZA": "ZAR",
}
# EU countries → EUR
_EU = {"DE","FR","ES","IT","NL","BE","AT","PT","GR","FI","IE","LU","SK","SI","EE","LV","LT","MT","CY","HR"}


def _ascii(s: str) -> str:
    """Strip accents for keyword matching."""
    return unicodedata.normalize("NFD", (s or "")).encode("ascii", "ignore").decode()


def _estimate_capacity(venue_name: str) -> int:
    """Heuristic: guess venue size from its name (accent-normalized)."""
    if not venue_name:
        return 1000
    lower = _ascii(venue_name).lower()
    for keyword, cap in VENUE_SIZE_MAP.items():
        if keyword in lower:
            return cap
    return 1000


def _infer_currency(country_code: str, price_ranges: list) -> str:
    """Get currency from price data, or infer from country code."""
    if price_ranges and price_ranges[0].get("currency"):
        return price_ranges[0]["currency"]
    cc = (country_code or "").upper()
    if cc in _COUNTRY_CURRENCY:
        return _COUNTRY_CURRENCY[cc]
    if cc in _EU:
        return "EUR"
    return "USD"


async def _get_attraction_id(artist_name: str, client: httpx.AsyncClient) -> str | None:
    """
    Find the Ticketmaster attraction ID for an artist.
    Using attractionId is far more accurate than keyword search — it avoids
    matching tribute acts, festivals, or events that just mention the artist name.
    """
    try:
        r = await client.get(
            f"{BASE_URL}/attractions.json",
            params={
                "apikey": os.environ.get("TICKETMASTER_API_KEY", ""),
                "keyword": artist_name,
                "classificationName": "music",
                "size": 5,
            },
        )
        if r.status_code != 200:
            return None
        attractions = r.json().get("_embedded", {}).get("attractions", [])
        if not attractions:
            return None
        # Prefer exact name match (accent-normalized)
        norm_target = _ascii(artist_name).lower()
        for att in attractions:
            if _ascii(att.get("name", "")).lower() == norm_target:
                return att["id"]
        # Fallback: first result
        return attractions[0]["id"]
    except Exception:
        return None


async def get_upcoming_events(artist_name: str, max_results: int = 50) -> list[dict]:
    """
    Fetch upcoming events globally for an artist.

    Strategy:
    1. Look up the artist's Ticketmaster attraction ID (more accurate than keyword search).
    2. Fetch events by attractionId — this covers all TM markets worldwide.
    3. Fall back to keyword search if no attractionId found.
    """
    api_key = os.environ.get("TICKETMASTER_API_KEY", "")
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(timeout=12) as client:
        attraction_id = await _get_attraction_id(artist_name, client)

        # Build query params
        params: dict = {
            "apikey": api_key,
            "classificationName": "music",
            "size": min(max_results, 200),
            "sort": "date,asc",
            "startDateTime": now_iso,   # only future events
        }
        if attraction_id:
            params["attractionId"] = attraction_id
        else:
            # Keyword fallback — less accurate but better than nothing
            params["keyword"] = artist_name

        try:
            r = await client.get(f"{BASE_URL}/events.json", params=params)
        except Exception:
            return []

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

            if not date_str:
                continue  # skip events with no date

            ticket_url = ev.get("url", "")
            price_ranges = ev.get("priceRanges", [])
            min_price = price_ranges[0].get("min") if price_ranges else None
            max_price = price_ranges[0].get("max") if price_ranges else None
            currency = _infer_currency(country_code, price_ranges)

            try:
                lat = float(location.get("latitude") or 0)
                lon = float(location.get("longitude") or 0)
            except (ValueError, TypeError):
                lat, lon = 0.0, 0.0

            results.append({
                "name": ev.get("name", ""),
                "date": date_str,
                "venue_name": venue_name,
                "city": city,
                "country": country,
                "country_code": country_code,
                "lat": lat,
                "lon": lon,
                "ticket_url": ticket_url,
                "estimated_capacity": _estimate_capacity(venue_name),
                "min_price": min_price,
                "max_price": max_price,
                "currency": currency,
            })
        return results
