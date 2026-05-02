import unicodedata
import httpx


def _normalize(s: str) -> str:
    """Lowercase + strip accents for fuzzy name comparison."""
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()

BASE_URL = "https://musicbrainz.org/ws/2"
HEADERS = {
    # MusicBrainz requires a descriptive User-Agent
    "User-Agent": "SoundCardMusic/1.0 (sebastianpomi@gmail.com)",
    "Accept": "application/json",
}

COUNTRY_NAMES = {
    "US": "United States", "GB": "United Kingdom", "ES": "Spain",
    "DE": "Germany", "FR": "France", "IT": "Italy", "BR": "Brazil",
    "MX": "Mexico", "AR": "Argentina", "CO": "Colombia", "PR": "Puerto Rico",
    "AU": "Australia", "CA": "Canada", "JP": "Japan", "KR": "South Korea",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
    "NL": "Netherlands", "BE": "Belgium", "AT": "Austria", "CH": "Switzerland",
    "PL": "Poland", "CZ": "Czech Republic", "RU": "Russia", "UA": "Ukraine",
    "TR": "Turkey", "IN": "India", "ID": "Indonesia", "PH": "Philippines",
    "ZA": "South Africa", "NG": "Nigeria", "CL": "Chile", "PE": "Peru",
    "VE": "Venezuela", "UY": "Uruguay", "PT": "Portugal", "IE": "Ireland",
    "NZ": "New Zealand", "SG": "Singapore", "MY": "Malaysia",
    "XW": "Worldwide", "XE": "Europe",
}

COUNTRY_FLAGS = {
    "US": "🇺🇸", "GB": "🇬🇧", "ES": "🇪🇸", "DE": "🇩🇪", "FR": "🇫🇷",
    "IT": "🇮🇹", "BR": "🇧🇷", "MX": "🇲🇽", "AR": "🇦🇷", "CO": "🇨🇴",
    "PR": "🇵🇷", "AU": "🇦🇺", "CA": "🇨🇦", "JP": "🇯🇵", "KR": "🇰🇷",
    "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰", "FI": "🇫🇮", "NL": "🇳🇱",
    "BE": "🇧🇪", "AT": "🇦🇹", "CH": "🇨🇭", "PL": "🇵🇱", "CZ": "🇨🇿",
    "RU": "🇷🇺", "UA": "🇺🇦", "TR": "🇹🇷", "IN": "🇮🇳", "ID": "🇮🇩",
    "PH": "🇵🇭", "ZA": "🇿🇦", "NG": "🇳🇬", "CL": "🇨🇱", "PE": "🇵🇪",
    "VE": "🇻🇪", "UY": "🇺🇾", "PT": "🇵🇹", "IE": "🇮🇪", "NZ": "🇳🇿",
    "SG": "🇸🇬", "MY": "🇲🇾",
}


async def get_artist_metadata(artist_name: str, canonical_name: str | None = None) -> dict:
    """
    Returns: country_code, country_name, country_flag, artist_type (Person/Group),
             begin_year (debut/birth year), area (origin city/region).
    All fields optional — returns {} if nothing found.
    """
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        try:
            r = await client.get(
                f"{BASE_URL}/artist/",
                params={
                    "query": f'artist:"{artist_name}"',
                    "fmt": "json",
                    "limit": 5,
                },
            )
            if r.status_code != 200:
                return {}
            artists = r.json().get("artists", [])
        except Exception:
            return {}

    if not artists:
        return {}

    # Pick best match using MB relevance score + accent-normalized name comparison
    # canonical_name (from Spotify) is more accurate than the raw user query
    search_name = canonical_name or artist_name
    norm_search = _normalize(search_name)
    best = None

    # Pass 1: normalized exact match + high score
    for a in artists:
        norm_a = _normalize(a.get("name", ""))
        if norm_a == norm_search and int(a.get("score", 0)) >= 85:
            best = a
            break

    # Pass 2: normalized exact match, any score
    if not best:
        for a in artists:
            if _normalize(a.get("name", "")) == norm_search:
                best = a
                break

    # Pass 3: highest-scoring result, only if score >= 90 (very confident)
    if not best:
        top = max(artists, key=lambda a: int(a.get("score", 0)))
        if int(top.get("score", 0)) >= 90:
            best = top

    if not best:
        return {}  # Don't guess when confidence is low

    country_code = best.get("country", "") or ""
    begin = best.get("life-span", {}).get("begin", "") or ""
    begin_year = begin[:4] if begin else None

    # Prefer begin-area (birth city/founding city) over area (country area)
    area = (
        best.get("begin-area", {}).get("name")
        or best.get("area", {}).get("name")
        or None
    )

    country_name = COUNTRY_NAMES.get(country_code, country_code) if country_code else None
    country_flag = COUNTRY_FLAGS.get(country_code, "") if country_code else ""

    artist_type = best.get("type", None)  # "Person", "Group", "Orchestra", etc.

    return {
        "country_code": country_code or None,
        "country_name": country_name,
        "country_flag": country_flag or None,
        "artist_type": artist_type,
        "begin_year": begin_year,
        "origin_area": area,
    }
