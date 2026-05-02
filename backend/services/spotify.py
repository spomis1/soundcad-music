import os
import time
import logging
import httpx

logger = logging.getLogger(__name__)

_token: str | None = None
_token_expires: float = 0


async def _get_token() -> str:
    global _token, _token_expires
    if _token and time.time() < _token_expires - 60:
        return _token
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]),
        )
        r.raise_for_status()
        body = r.json()
        _token = body["access_token"]
        _token_expires = time.time() + body["expires_in"]
    return _token


async def search_artist(name: str) -> dict | None:
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/search",
            params={"q": name, "type": "artist", "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            return None
        items = r.json().get("artists", {}).get("items", [])
        return items[0] if items else None


async def get_artist_data(name: str) -> dict:
    try:
        artist = await search_artist(name)
    except Exception as e:
        logger.error(f"Spotify search failed for '{name}': {e}")
        return {}
    if not artist:
        logger.warning(f"Spotify: no artist found for '{name}'")
        return {}

    spotify_id = artist["id"]
    token = await _get_token()

    async with httpx.AsyncClient() as client:
        # Top tracks
        r = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_id}/top-tracks",
            params={"market": "US"},
            headers={"Authorization": f"Bearer {token}"},
        )
        top_tracks = r.json().get("tracks", []) if r.status_code == 200 else []

        # Related artists
        r2 = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_id}/related-artists",
            headers={"Authorization": f"Bearer {token}"},
        )
        related = r2.json().get("artists", []) if r2.status_code == 200 else []

        # Albums (only full albums + singles, exclude compilations)
        r3 = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_id}/albums",
            params={"include_groups": "album,single", "market": "US", "limit": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        albums_raw = r3.json().get("items", []) if r3.status_code == 200 else []

    # Build country presence from available_markets of top tracks
    all_markets: set[str] = set()
    for track in top_tracks:
        all_markets.update(track.get("available_markets", []))

    MARKET_NAMES = {
        "US": "United States", "GB": "United Kingdom", "DE": "Germany",
        "BR": "Brazil", "FR": "France", "MX": "Mexico", "AR": "Argentina",
        "ES": "Spain", "AU": "Australia", "CA": "Canada", "JP": "Japan",
        "KR": "South Korea", "IT": "Italy", "NL": "Netherlands", "PL": "Poland",
        "SE": "Sweden", "RU": "Russia", "TR": "Turkey", "IN": "India",
        "ID": "Indonesia", "CL": "Chile", "CO": "Colombia", "PE": "Peru",
        "VE": "Venezuela", "UY": "Uruguay", "BO": "Bolivia", "PY": "Paraguay",
        "EC": "Ecuador", "CR": "Costa Rica", "PA": "Panama", "DO": "Dominican Republic",
        "GT": "Guatemala", "HN": "Honduras", "SV": "El Salvador", "NI": "Nicaragua",
        "PR": "Puerto Rico", "CU": "Cuba", "PT": "Portugal", "RO": "Romania",
        "HU": "Hungary", "CZ": "Czech Republic", "SK": "Slovakia", "HR": "Croatia",
        "BG": "Bulgaria", "GR": "Greece", "FI": "Finland", "NO": "Norway",
        "DK": "Denmark", "BE": "Belgium", "AT": "Austria", "CH": "Switzerland",
        "ZA": "South Africa", "NG": "Nigeria", "EG": "Egypt", "MA": "Morocco",
        "PH": "Philippines", "TH": "Thailand", "MY": "Malaysia", "SG": "Singapore",
        "TW": "Taiwan", "HK": "Hong Kong", "IL": "Israel", "AE": "United Arab Emirates",
        "SA": "Saudi Arabia",
    }

    country_presence = []
    for i, code in enumerate(sorted(all_markets)):
        if code in MARKET_NAMES:
            country_presence.append({
                "country": MARKET_NAMES[code],
                "country_code": code,
                "rank": i + 1,
                "listeners": None,
            })

    # Deduplicate albums by name, sort by date desc, full albums first (max 12)
    seen_names = set()
    albums_full = []
    albums_single = []
    for a in sorted(albums_raw, key=lambda x: x.get("release_date", ""), reverse=True):
        aname = a.get("name", "")
        if aname.lower() in seen_names:
            continue
        seen_names.add(aname.lower())
        img = a["images"][0]["url"] if a.get("images") else None
        entry = {
            "name": aname,
            "year": a.get("release_date", "")[:4],
            "total_tracks": a.get("total_tracks"),
            "image": img,
            "album_type": a.get("album_type"),
        }
        if a.get("album_type") == "album":
            albums_full.append(entry)
        else:
            albums_single.append(entry)

    # Show full albums first, pad with recent singles up to 12 total
    albums = (albums_full + albums_single)[:12]

    image_url = None
    if artist.get("images"):
        image_url = artist["images"][0]["url"]

    return {
        "spotify_id": spotify_id,
        "name": artist["name"],
        "followers": artist.get("followers", {}).get("total", 0),
        "popularity": artist.get("popularity", 0),
        "genres": artist.get("genres", []),
        "image_url": image_url,
        "country_presence": country_presence,
        "market_count": len(all_markets),
        "related_artists": [
            {"name": a["name"], "popularity": a.get("popularity", 0)}
            for a in related[:6]
        ],
        "top_tracks": [
            {
                "name": t["name"],
                "popularity": t.get("popularity", 0),
                "preview_url": t.get("preview_url"),
            }
            for t in top_tracks[:5]
        ],
        "albums": albums,
    }
